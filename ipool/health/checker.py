import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
from sqlalchemy import select, update

from ipool.config import settings
from ipool.node.models import ProxyNode, HealthCheckResult
from ipool.storage.database import get_session

logger = logging.getLogger(__name__)


class HealthChecker:
    """代理健康状态检查器"""
    
    def __init__(self):
        self.check_url = settings.health_check_url
        self.check_interval = settings.health_check_interval
        self.timeout = settings.health_check_timeout
        self._running = False
        
    async def start(self):
        """启动健康检查循环"""
        if self._running:
            return
            
        self._running = True
        logger.info(f"健康检查服务启动，检查URL: {self.check_url}, 间隔: {self.check_interval}秒")
        
        while self._running:
            try:
                # 检查所有活跃的代理
                await self._check_all_proxies()
                
                # 等待下一次检查
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查过程中发生错误: {str(e)}", exc_info=True)
                await asyncio.sleep(10)  # 出错后短暂暂停
    
    async def stop(self):
        """停止健康检查循环"""
        self._running = False
        logger.info("健康检查服务已停止")
    
    async def _check_all_proxies(self):
        """检查所有代理的健康状态"""
        async with get_session() as session:
            # 获取所有活跃的代理节点
            result = await session.execute(
                select(ProxyNode).where(ProxyNode.is_active == True)
            )
            proxies = result.scalars().all()
            
            if not proxies:
                logger.info("没有活跃的代理节点需要检查")
                return
            
            # 并发检查所有代理
            check_tasks = [self._check_proxy(proxy) for proxy in proxies]
            results = await asyncio.gather(*check_tasks, return_exceptions=True)
            
            # 更新数据库
            for proxy, result in zip(proxies, results):
                if isinstance(result, Exception):
                    logger.error(f"检查代理 {proxy.host}:{proxy.port} 时发生错误: {str(result)}")
                    continue
                    
                try:
                    # 更新代理状态
                    proxy.is_healthy = result.success
                    proxy.response_time = result.response_time if result.success else 10000
                    proxy.last_check = datetime.utcnow()
                    
                    # 如果失败，降低成功率
                    if not result.success:
                        proxy.success_rate = max(0, proxy.success_rate - 5)
                    else:
                        # 如果成功，提高成功率，但不超过100
                        proxy.success_rate = min(100, proxy.success_rate + 1)
                        
                    logger.debug(f"代理 {proxy.host}:{proxy.port} 健康检查: {'成功' if result.success else '失败'}, "
                                f"响应时间: {result.response_time:.2f}ms, 成功率: {proxy.success_rate}%")
                    
                except Exception as e:
                    logger.error(f"更新代理 {proxy.host}:{proxy.port} 状态时出错: {str(e)}")
            
            # 提交更改
            await session.commit()
            logger.info(f"完成 {len(proxies)} 个代理节点的健康检查")
    
    async def _check_proxy(self, proxy: ProxyNode) -> HealthCheckResult:
        """检查单个代理节点的健康状态"""
        result = HealthCheckResult(success=False, response_time=10000)
        
        # 构建代理URL
        proxy_url = f"{proxy.protocol}://"
        if proxy.username and proxy.password:
            proxy_url += f"{proxy.username}:{proxy.password}@"
        proxy_url += f"{proxy.host}:{proxy.port}"
        
        start_time = time.time()
        try:
            # 配置代理连接
            async with aiohttp.ClientSession() as session:
                # 使用代理请求目标URL
                async with session.get(
                    self.check_url,
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    allow_redirects=True
                ) as response:
                    # 检查是否成功
                    if response.status == 200:
                        # 计算响应时间（毫秒）
                        response_time = (time.time() - start_time) * 1000
                        result = HealthCheckResult(
                            success=True,
                            response_time=response_time
                        )
                    else:
                        result = HealthCheckResult(
                            success=False,
                            response_time=10000,
                            error_message=f"HTTP状态码: {response.status}"
                        )
                        
        except asyncio.TimeoutError:
            result = HealthCheckResult(
                success=False,
                response_time=10000,
                error_message="请求超时"
            )
        except Exception as e:
            result = HealthCheckResult(
                success=False,
                response_time=10000,
                error_message=str(e)
            )
            
        return result