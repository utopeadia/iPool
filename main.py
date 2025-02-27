#!/usr/bin/env python
import asyncio
import logging
import os
import uvicorn
from dotenv import load_dotenv

from ipool.config import settings
from ipool.api.app import create_app
from ipool.protocols.socks5 import Socks5Server
from ipool.protocols.http import HttpProxyServer
from ipool.health.checker import HealthChecker
from ipool.storage.database import init_db

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.log_file)
    ]
)
logger = logging.getLogger(__name__)


async def start_services():
    """启动所有服务组件"""
    # 初始化数据库
    await init_db()
    
    # 创建FastAPI应用
    app = create_app()
    
    # 启动健康检查器
    health_checker = HealthChecker()
    asyncio.create_task(health_checker.start())
    
    # 启动Socks5服务器
    socks5_server = Socks5Server(host=settings.host, port=settings.socks5_port)
    asyncio.create_task(socks5_server.start())
    
    # 启动HTTP代理服务器
    http_proxy = HttpProxyServer(host=settings.host, port=settings.http_proxy_port)
    asyncio.create_task(http_proxy.start())
    
    # 启动API服务器
    config = uvicorn.Config(
        app=app,
        host=settings.host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    # 打印欢迎信息
    logger.info("="*50)
    logger.info("iPool 代理池系统启动中...")
    logger.info(f"API服务运行于: http://{settings.host}:{settings.api_port}")
    logger.info(f"Socks5服务运行于: {settings.host}:{settings.socks5_port}")
    logger.info(f"HTTP代理服务运行于: {settings.host}:{settings.http_proxy_port}")
    logger.info("="*50)
    
    try:
        # 启动所有服务
        asyncio.run(start_services())
    except KeyboardInterrupt:
        logger.info("正在关闭服务...")
    except Exception as e:
        logger.error(f"启动失败: {str(e)}", exc_info=True)
    finally:
        logger.info("服务已关闭")
