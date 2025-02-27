import logging
from typing import Optional, Dict, List
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipool.scheduler.base import SchedulerBase
from ipool.node.models import ProxyNode
from ipool.storage.database import get_session

logger = logging.getLogger(__name__)


class RoundRobinScheduler(SchedulerBase):
    """轮询加权负载均衡调度器"""
    
    def __init__(self):
        # 记录上次使用时间
        self._last_used: Dict[int, float] = {}
    
    async def next_proxy(self) -> Optional[ProxyNode]:
        """轮询获取一个代理节点，考虑权重"""
        async with get_session() as session:
            # 获取所有活跃且健康的代理节点
            result = await session.execute(
                select(ProxyNode).where(
                    ProxyNode.is_active == True,
                    ProxyNode.is_healthy == True
                ).order_by(ProxyNode.weight.desc())
            )
            proxies = result.scalars().all()
            
            if not proxies:
                logger.warning("没有可用的健康代理节点")
                return None
            
            # 找到当前负载最小的代理节点
            best_proxy = None
            min_load = float('inf')
            
            for proxy in proxies:
                # 计算相对负载，考虑节点权重和当前连接数
                relative_load = proxy.current_connections / max(1, proxy.weight)
                
                # 如果负载相同，选择最近最少使用的节点
                if relative_load < min_load or (
                    relative_load == min_load and
                    self._last_used.get(proxy.id, 0) < self._last_used.get(best_proxy.id if best_proxy else -1, 0)
                ):
                    min_load = relative_load
                    best_proxy = proxy
            
            if best_proxy:
                # 更新连接计数和最后使用时间
                best_proxy.current_connections += 1
                self._last_used[best_proxy.id] = time.time()
                await session.commit()
                
                logger.debug(f"轮询选择代理节点: {best_proxy.host}:{best_proxy.port} (权重: {best_proxy.weight}, 当前连接: {best_proxy.current_connections})")
                return best_proxy
            
            return None
    
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
