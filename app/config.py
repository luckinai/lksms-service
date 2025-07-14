from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # Basic Auth配置
    basic_auth_username: str = "admin"
    basic_auth_password: str = "password"

    # 数据库配置参数
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "lksms_db"
    postgres_user: str = "lksms_user"
    postgres_password: str = "lksms_password"
    
    # 应用配置
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    
    # 日志配置
    log_level: str = "INFO"

    # 重试配置
    max_retry_count: int = 3
    retry_delay_minutes: int = 5
    processing_timeout_minutes: int = 30

    # 文档配置
    enable_docs: bool = True

    @property
    def database_url(self) -> str:
        """动态构建数据库连接URL"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()
