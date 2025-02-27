from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import os
import logging
from typing import List, Optional

from ipool.config import settings
from ipool.node.models import ProxyNodeResponse, ProxyNodeCreate, ProxyNodeUpdate, ProxyProtocol
from ipool.node.repository import ProxyNodeRepository
from ipool.scheduler.base import get_scheduler, set_scheduler
from ipool.scheduler.random import RandomScheduler
from ipool.scheduler.round_robin import RoundRobinScheduler
from ipool.scheduler.health_first import HealthFirstScheduler
from ipool.health.checker import HealthChecker

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="iPool API",
        description="代理池系统API接口",
        version="0.1.0",
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 在此处注册API路由
    register_routes(app)
    
    # 尝试挂载静态文件（如果存在）
    try:
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend/dist")
        if os.path.exists(static_dir):
            app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
            
            @app.get("/", response_class=HTMLResponse, include_in_schema=False)
            async def get_index():
                return FileResponse(os.path.join(static_dir, "index.html"))
    except Exception as e:
        logger.warning(f"挂载静态文件失败: {str(e)}")
    
    return app


def register_routes(app: FastAPI):
    """注册API路由"""
    
    # 健康检查端点
    @app.get("/api/health")
    async def health_check():
        return {"status": "ok", "version": "0.1.0"}
    
    # == 代理节点管理 ==
    
    @app.post("/api/nodes", response_model=ProxyNodeResponse, status_code=status.HTTP_201_CREATED)
    async def create_node(node: ProxyNodeCreate):
        """创建新的代理节点"""
        return await ProxyNodeRepository.create(node)
    
    @app.get("/api/nodes", response_model=List[ProxyNodeResponse])
    async def get_nodes(
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_healthy: Optional[bool] = None,
        protocol: Optional[ProxyProtocol] = None,
        country: Optional[str] = None,
        search: Optional[str] = None
    ):
        """获取代理节点列表"""
        return await ProxyNodeRepository.get_all(
            skip=skip,
            limit=limit,
            is_active=is_active,
            is_healthy=is_healthy,
            protocol=protocol.value if protocol else None,
            country=country,
            search=search
        )
    
    @app.get("/api/nodes/{node_id}", response_model=ProxyNodeResponse)
    async def get_node(node_id: int):
        """获取特定代理节点详情"""
        node = await ProxyNodeRepository.get_by_id(node_id)
        if not node:
            raise HTTPException(status_code=404, detail="代理节点未找到")
        return node
    
    @app.put("/api/nodes/{node_id}", response_model=ProxyNodeResponse)
    async def update_node(node_id: int, node_data: ProxyNodeUpdate):
        """更新代理节点"""
        updated_node = await ProxyNodeRepository.update(node_id, node_data)
        if not updated_node:
            raise HTTPException(status_code=404, detail="代理节点未找到")
        return updated_node
    
    @app.delete("/api/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_node(node_id: int):
        """删除代理节点"""
        success = await ProxyNodeRepository.delete(node_id)
        if not success:
            raise HTTPException(status_code=404, detail="代理节点未找到")
    
    # == 调度策略管理 ==
    
    @app.get("/api/scheduler")
    async def get_scheduler_info():
        """获取当前调度策略"""
        scheduler = get_scheduler()
        return {"name": scheduler.__class__.__name__}
    
    @app.put("/api/scheduler")
    async def update_scheduler(scheduler_type: str):
        """更新调度策略"""
        scheduler_map = {
            "random": RandomScheduler,
            "round_robin": RoundRobinScheduler,
            "health_first": HealthFirstScheduler
        }
        
        if scheduler_type not in scheduler_map:
            raise HTTPException(status_code=400, detail=f"不支持的调度器类型: {scheduler_type}")
        
        scheduler = set_scheduler(scheduler_map[scheduler_type])
        return {"name": scheduler.__class__.__name__}
    
    # == 统计信息 ==
    
    @app.get("/api/stats")
    async def get_statistics():
        """获取代理池统计信息"""
        return await ProxyNodeRepository.get_statistics()
    
    # == 手动触发健康检查 ==
    
    @app.post("/api/check/all")
    async def trigger_health_check():
        """手动触发所有节点健康检查"""
        checker = HealthChecker()
        await checker._check_all_proxies()
        return {"status": "ok", "message": "健康检查已触发"}
