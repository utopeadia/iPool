from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field, IPvAnyAddress

Base = declarative_base()


class ProxyProtocol(str, Enum):
    """代理协议类型"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class ProxyNode(Base):
    """代理节点数据模型"""
    __tablename__ = "proxy_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    protocol = Column(SQLEnum(ProxyProtocol), nullable=False)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    
    # 节点状态信息
    is_active = Column(Boolean, default=True)
    is_healthy = Column(Boolean, default=True)
    response_time = Column(Float, default=0.0)  # 毫秒
    success_rate = Column(Float, default=100.0)  # 百分比
    
    # 调度相关
    weight = Column(Integer, default=1)
    max_connections = Column(Integer, default=100)
    current_connections = Column(Integer, default=0)
    
    # 元数据
    country = Column(String, nullable=True)
    region = Column(String, nullable=True)
    tags = Column(String, nullable=True)  # 逗号分隔的标签
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_check = Column(DateTime, nullable=True)


# Pydantic 模型用于 API
class ProxyNodeCreate(BaseModel):
    name: str | None = None
    host: str
    port: int
    protocol: ProxyProtocol
    username: str | None = None
    password: str | None = None
    weight: int = 1
    max_connections: int = 100
    country: str | None = None
    region: str | None = None
    tags: str | None = None


class ProxyNodeUpdate(BaseModel):
    name: str | None = None
    host: str | None = None
    port: int | None = None
    protocol: ProxyProtocol | None = None
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None
    weight: int | None = None
    max_connections: int | None = None
    country: str | None = None
    region: str | None = None
    tags: str | None = None


class ProxyNodeResponse(BaseModel):
    id: int
    name: str | None = None
    host: str
    port: int
    protocol: ProxyProtocol
    username: str | None = None
    is_active: bool
    is_healthy: bool
    response_time: float
    success_rate: float
    weight: int
    max_connections: int
    current_connections: int
    country: str | None = None
    region: str | None = None
    tags: str | None = None
    created_at: datetime
    updated_at: datetime
    last_check: datetime | None = None
    
    class Config:
        orm_mode = True


class HealthCheckResult(BaseModel):
    success: bool
    response_time: float  # 毫秒
    error_message: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
