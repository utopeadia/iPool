import logging
from abc import ABC, abstractmethod
from typing import Optional, Type

from ipool.node.models import ProxyNode

logger = logging.getLogger(__name__)

# 全局调度器实例
_current_scheduler = None


def get_scheduler():
    """获取当前配置的调度器实例"""
    global _current_scheduler
    if _current_scheduler is None:
        # 默认使用健康优先调度器
        from ipool.scheduler.health_first import HealthFirstScheduler
        _current_scheduler = HealthFirstScheduler()
        logger.info(f"使用默认调度器: {_current_scheduler.__class__.__name__}")
    return _current_scheduler


def set_scheduler(scheduler_class: Type["SchedulerBase"]):
    """设置新的调度器类型"""
    global _current_scheduler
    _current_scheduler = scheduler_class()
    logger.info(f"设置新的调度器: {_current_scheduler.__class__.__name__}")
    return _current_scheduler


class SchedulerBase(ABC):
    """代理调度器基类"""
    
    @abstractmethod
    async def next_proxy(self) -> Optional[ProxyNode]:
        """获取下一个代理节点"""
        pass
    
    @abstractmethod
    async def report_success(self, proxy_node: ProxyNode, response_time: float):
        """报告代理请求成功"""
        pass
    
    @abstractmethod
    async def report_failure(self, proxy_node: ProxyNode, error: str):
        """报告代理请求失败"""
        pass
