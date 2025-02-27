import logging
import random
from typing import Optional, List, Dict
import time

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ipool.scheduler.base import SchedulerBase
from ipool.node.models import ProxyNode
from ipool.storage.database import get_session

logger = logging.getLogger(__name__)


class HealthFirstScheduler(SchedulerBase):
    """健康状态优先的调度器"""
    
    def __init__(self):
        # 健康得分缓存
        self._health_scores: Dict[int, float] = {}
        # 最后更新时间
        self._last_updated: Dict[int, float] = {}
        # 缓存有效期（秒）
        self._cache_ttl = 60
    
    async def next_proxy(self) -> Optional[ProxyNode]:
        """基于健康状态选择代理节点"""
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
            
            # 计算健康得分并选择最佳节点
            best_proxies = []
            best_score = -float('inf')
            
            for proxy in proxies:
                # 获取或计算健康得分
                score = self._get_health_score(proxy)
                
                if score > best_score:
                    best_score = score
                    best_proxies = [proxy]
                elif score == best_score:
                    best_proxies.append(proxy)
            
            # 从得分相同的最佳节点中随机选择
            selected_proxy = random.choice(best_proxies)
            
            # 更新连接计数
            selected_proxy.current_connections += 1
            await session.commit()
            
            logger.debug(f"健康优先选择代理节点: {selected_proxy.host}:{selected_proxy.port} (得分: {best_score:.2f})")
            return selected_proxy
    
    def _get_health_score(self, proxy: ProxyNode) -> float:
        """计算代理节点的健康得分"""
        proxy_id = proxy.id
        now = time.time()
        
        # 如果缓存有效，直接返回缓存的得分
        if proxy_id in self._health_scores and now - self._last_updated.get(proxy_id, 0) < self._cache_ttl:
            return self._health_scores[proxy_id]
        
        # 计算综合健康得分
        # 1. 响应时间分数 (较低的响应时间给予更高分数)
        response_score = max(0, 100 - min(proxy.response_time, 1000) / 10)
        
        # 2. 成功率分数
        success_score = proxy.success_rate
        
        # 3. 负载分数 (较低的负载给予更高分数)
        load_ratio = proxy.current_connections / max(proxy.max_connections, 1)
        load_score = 100 * (1 - min(load_ratio, 1))
        
        # 4. 权重分数
        weight_score = min(proxy.weight * 10, 100)
        
        # 综合得分 (可根据需要调整权重)
        final_score = (
            response_score * 0.4 + 
            success_score * 0.3 + 
            load_score * 0.2 + 
            weight_score * 0.1
        )
        
        # 更新缓存
        self._health_scores[proxy_id] = final_score
        self._last_updated[proxy_id] = now
        
        return final_score
    
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
                
                # 更新响应时间 (加权平均)
                db_proxy.response_time = 0.7 * db_proxy.response_time + 0.3 * response_time
                
                # 清除缓存，强制重新计算得分
                if db_proxy.id in self._health_scores:
                    del self._health_scores[db_proxy.id]
                
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
                
                # 更新成功率
                db_proxy.success_rate = max(0, db_proxy.success_rate - 1)
                
                # 清除缓存，强制重新计算得分
                if db_proxy.id in self._health_scores:
                    del self._health_scores[db_proxy.id]
                
                logger.warning(f"代理 {db_proxy.host}:{db_proxy.port} 请求失败: {error}")
                await session.commit()
