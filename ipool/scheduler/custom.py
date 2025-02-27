import logging
import json
import ast
from typing import Optional, Dict, List, Any
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipool.scheduler.base import SchedulerBase
from ipool.node.models import ProxyNode
from ipool.storage.database import get_session

logger = logging.getLogger(__name__)


class CustomRuleScheduler(SchedulerBase):
    """自定义规则引擎调度器"""
    
    def __init__(self, rules: Optional[List[Dict[str, Any]]] = None):
        """
        初始化自定义规则调度器
        
        规则格式示例:
        [
            {
                "name": "高响应速度优先",
                "condition": "node.response_time < 100 and node.success_rate > 90",
                "priority": 100
            },
            {
                "name": "特定国家/地区优先",
                "condition": "node.country == 'US' or node.country == 'JP'",
                "priority": 80
            },
            {
                "name": "标签匹配",
                "condition": "'premium' in (node.tags or '')",
                "priority": 60
            }
        ]
        """
        self.rules = rules or []
        self._rule_cache = {}  # 缓存编译后的规则
    
    async def next_proxy(self) -> Optional[ProxyNode]:
        """基于自定义规则选择代理节点"""
        async with get_session() as session:
            # 获取所有活跃且健康的代理节点
            result = await session.execute(
                select(ProxyNode).where(
                    ProxyNode.is_active == True,
                    ProxyNode.is_healthy == True
                )
            )
            proxies = result.scalars().all()
            
            if not proxies:
                logger.warning("没有可用的健康代理节点")
                return None
            
            # 应用规则并评分
            scored_proxies = []
            for proxy in proxies:
                score = self._evaluate_rules(proxy)
                scored_proxies.append((proxy, score))
            
            # 按分数降序排序
            scored_proxies.sort(key=lambda x: x[1], reverse=True)
            
            if scored_proxies:
                selected_proxy = scored_proxies[0][0]
                
                # 更新连接计数
                selected_proxy.current_connections += 1
                await session.commit()
                
                logger.debug(f"自定义规则选择代理节点: {selected_proxy.host}:{selected_proxy.port} (得分: {scored_proxies[0][1]})")
                return selected_proxy
            
            return None
    
    def _evaluate_rules(self, proxy: ProxyNode) -> float:
        """
        评估代理节点对所有规则的符合程度
        返回总分数
        """
        total_score = 0.0
        
        for rule in self.rules:
            try:
                # 获取规则属性
                condition = rule.get("condition", "True")
                priority = float(rule.get("priority", 1))
                
                # 评估条件
                if self._eval_condition(proxy, condition):
                    total_score += priority
            except Exception as e:
                logger.error(f"规则评估出错: {str(e)}")
        
        return total_score
    
    def _eval_condition(self, proxy: ProxyNode, condition: str) -> bool:
        """
        评估代理节点是否满足条件
        使用Python语法允许灵活的条件表达式
        """
        try:
            # 首先尝试从缓存获取已编译的规则
            if condition in self._rule_cache:
                condition_func = self._rule_cache[condition]
            else:
                # 编译条件表达式为可调用函数
                condition_code = f"lambda node: {condition}"
                condition_func = eval(condition_code)
                # 缓存编译后的函数
                self._rule_cache[condition] = condition_func
            
            # 执行条件评估
            return condition_func(proxy)
        except Exception as e:
            logger.error(f"条件表达式'{condition}'评估失败: {str(e)}")
            return False
    
    async def report_success(self, proxy_node: ProxyNode, response_time: float):
        """报告代理请求成功"""
        async with get_session() as session:
            # 获取最新的节点数据
            result = await session.execute(
                select(ProxyNode).where(ProxyNode.id == proxy_node.id)
            )
            db_proxy = result.scalars().first()
            
            if db_proxy:
                # 更新连接计数
                db_proxy.current_connections = max(0, db_proxy.current_connections - 1)
                await session.commit()
    
    async def report_failure(self, proxy_node: ProxyNode, error: str):
        """报告代理请求失败"""
        async with get_session() as session:
            # 获取最新的节点数据
            result = await session.execute(
                select(ProxyNode).where(ProxyNode.id == proxy_node.id)
            )
            db_proxy = result.scalars().first()
            
            if db_proxy:
                # 更新连接计数
                db_proxy.current_connections = max(0, db_proxy.current_connections - 1)
                logger.warning(f"代理 {db_proxy.host}:{db_proxy.port} 请求失败: {error}")
                await session.commit()
    
    def add_rule(self, name: str, condition: str, priority: float):
        """添加新规则"""
        self.rules.append({
            "name": name,
            "condition": condition,
            "priority": priority
        })
        # 清除受影响的缓存
        if condition in self._rule_cache:
            del self._rule_cache[condition]
    
    def remove_rule(self, name: str):
        """移除指定名称的规则"""
        self.rules = [r for r in self.rules if r.get("name") != name]
        # 重置全部缓存
        self._rule_cache = {}
    
    def clear_rules(self):
        """清除所有规则"""
        self.rules = []
        self._rule_cache = {}