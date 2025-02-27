import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional

from ipool.scheduler.base import get_scheduler
from ipool.node.models import ProxyNode

logger = logging.getLogger(__name__)


class ProxyServer(ABC):
    """代理服务器基类"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.server = None
        self._running = False
        self.scheduler = get_scheduler()  # 获取当前配置的调度器
    
    async def start(self):
        """启动代理服务器"""
        self._running = True
        self.server = await self._create_server()
        logger.info(f"{self.__class__.__name__} 已启动于 {self.host}:{self.port}")
        
        try:
            await self._run_server()
        except asyncio.CancelledError:
            logger.info(f"{self.__class__.__name__} 任务被取消")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} 发生错误: {str(e)}", exc_info=True)
        finally:
            await self.stop()
    
    async def stop(self):
        """停止代理服务器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        
        self._running = False
        logger.info(f"{self.__class__.__name__} 已停止")
    
    async def get_proxy(self) -> Optional[ProxyNode]:
        """获取一个代理节点"""
        return await self.scheduler.next_proxy()
    
    @abstractmethod
    async def _create_server(self):
        """创建服务器实例"""
        pass
    
    @abstractmethod
    async def _run_server(self):
        """运行服务器主循环"""
        pass
    
    @abstractmethod
    async def handle_client(self, reader, writer):
        """处理客户端连接"""
        pass
