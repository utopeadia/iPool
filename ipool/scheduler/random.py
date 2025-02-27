import logging
import random
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipool.scheduler.base import SchedulerBase
from ipool.node.models import ProxyNode
from ipool.storage.database import get_session

logger = logging.getLogger(__name__)


class RandomScheduler(SchedulerBase):
    """随机选择代理节点的调度器"""
    
    async def next_proxy(self) -> Optional[ProxyNode]:
        """随机获取一个健康的代理节点"""
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
            
            # 随机选择一个节点
            selected_proxy = random.choice(proxies)
            logger.debug(f"随机选择代理节点: {selected_proxy.host}:{selected_proxy.port}")
            
            # 更新连接计数
            selected_proxy.current_connections += 1
            await session.commit()
            
            return selected_proxy
    
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
