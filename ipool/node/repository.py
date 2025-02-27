import logging
from typing import List, Optional, Dict, Any

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ipool.node.models import ProxyNode, ProxyNodeCreate, ProxyNodeUpdate
from ipool.storage.database import get_session

logger = logging.getLogger(__name__)


class ProxyNodeRepository:
    """代理节点仓库"""
    
    @staticmethod
    async def create(node_data: ProxyNodeCreate) -> ProxyNode:
        """创建新的代理节点"""
        async with get_session() as session:
            # 创建新的代理节点
            node = ProxyNode(
                name=node_data.name,
                host=node_data.host,
                port=node_data.port,
                protocol=node_data.protocol,
                username=node_data.username,
                password=node_data.password,
                weight=node_data.weight,
                max_connections=node_data.max_connections,
                country=node_data.country,
                region=node_data.region,
                tags=node_data.tags
            )
            
            # 添加到数据库
            session.add(node)
            await session.commit()
            await session.refresh(node)
            
            logger.info(f"创建新代理节点: {node.host}:{node.port}")
            return node
    
    @staticmethod
    async def get_by_id(node_id: int) -> Optional[ProxyNode]:
        """根据ID获取代理节点"""
        async with get_session() as session:
            result = await session.execute(
                select(ProxyNode).where(ProxyNode.id == node_id)
            )
            return result.scalars().first()
    
    @staticmethod
    async def get_all(
        skip: int = 0, 
        limit: int = 100, 
        is_active: Optional[bool] = None,
        is_healthy: Optional[bool] = None,
        protocol: Optional[str] = None,
        country: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[ProxyNode]:
        """获取所有代理节点"""
        async with get_session() as session:
            query = select(ProxyNode)
            
            # 应用过滤条件
            if is_active is not None:
                query = query.where(ProxyNode.is_active == is_active)
            
            if is_healthy is not None:
                query = query.where(ProxyNode.is_healthy == is_healthy)
            
            if protocol:
                query = query.where(ProxyNode.protocol == protocol)
            
            if country:
                query = query.where(ProxyNode.country == country)
            
            if search:
                search_term = f"%{search}%"
                query = query.where(
                    (ProxyNode.host.like(search_term)) |
                    (ProxyNode.name.like(search_term)) |
                    (ProxyNode.tags.like(search_term))
                )
            
            # 分页
            query = query.offset(skip).limit(limit)
            
            # 执行查询
            result = await session.execute(query)
            return result.scalars().all()
    
    @staticmethod
    async def update(node_id: int, node_data: ProxyNodeUpdate) -> Optional[ProxyNode]:
        """更新代理节点"""
        async with get_session() as session:
            # 先获取节点
            result = await session.execute(
                select(ProxyNode).where(ProxyNode.id == node_id)
            )
            node = result.scalars().first()
            
            if not node:
                return None
            
            # 更新字段
            update_data = node_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(node, key, value)
            
            await session.commit()
            await session.refresh(node)
            
            logger.info(f"更新代理节点 ID={node_id}: {node.host}:{node.port}")
            return node
    
    @staticmethod
    async def delete(node_id: int) -> bool:
        """删除代理节点"""
        async with get_session() as session:
            result = await session.execute(
                delete(ProxyNode).where(ProxyNode.id == node_id).returning(ProxyNode.id)
            )
            deleted = result.first()
            
            if not deleted:
                return False
            
            await session.commit()
            logger.info(f"删除代理节点 ID={node_id}")
            return True
    
    @staticmethod
    async def get_statistics() -> Dict[str, Any]:
        """获取代理节点统计信息"""
        async with get_session() as session:
            # 总节点数
            total_result = await session.execute(select(func.count(ProxyNode.id)))
            total_count = total_result.scalar() or 0
            
            # 活跃节点数
            active_result = await session.execute(
                select(func.count(ProxyNode.id)).where(ProxyNode.is_active == True)
            )
            active_count = active_result.scalar() or 0
            
            # 健康节点数
            healthy_result = await session.execute(
                select(func.count(ProxyNode.id)).where(
                    ProxyNode.is_active == True,
                    ProxyNode.is_healthy == True
                )
            )
            healthy_count = healthy_result.scalar() or 0
            
            # 平均响应时间
            avg_response_result = await session.execute(
                select(func.avg(ProxyNode.response_time)).where(
                    ProxyNode.is_active == True,
                    ProxyNode.is_healthy == True
                )
            )
            avg_response_time = avg_response_result.scalar() or 0
            
            # 按协议分组
            protocol_result = await session.execute(
                select(ProxyNode.protocol, func.count(ProxyNode.id))
                .group_by(ProxyNode.protocol)
            )
            protocol_stats = {p[0].value: p[1] for p in protocol_result.all()}
            
            # 按国家分组
            country_result = await session.execute(
                select(ProxyNode.country, func.count(ProxyNode.id))
                .where(ProxyNode.country != None)
                .group_by(ProxyNode.country)
            )
            country_stats = {c[0]: c[1] for c in country_result.all()}
            
            return {
                "total": total_count,
                "active": active_count,
                "healthy": healthy_count,
                "avg_response_time": round(avg_response_time, 2),
                "protocols": protocol_stats,
                "countries": country_stats
            }
