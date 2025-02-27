import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置设置"""
    # 服务配置
    host: str = "0.0.0.0"
    api_port: int = 8000
    socks5_port: int = 1080
    http_proxy_port: int = 8080
    debug: bool = False
    secret_key: str = "changeme_use_strong_secret_key"
    
    # 数据库配置
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ipool"
    db_user: str = "postgres"
    db_password: str = "password"
    
    # 数据库URL
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # 健康检查配置
    health_check_interval: int = 300
    health_check_url: str = "https://www.google.com"
    health_check_timeout: int = 10
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "ipool.log"
    
    # Web界面配置
    web_admin_user: str = "admin"
    web_admin_password: str = "admin"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()
