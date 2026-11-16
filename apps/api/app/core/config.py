"""应用配置：从环境变量 / .env 加载。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置项。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Prism API"
    app_env: str = "dev"
    debug: bool = True
    secret_key: str = "dev-secret-change-me"

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./data/prism.db"

    # Redis（可选）
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    access_token_expire_minutes: int = 60 * 24 * 7
    jwt_algorithm: str = "HS256"

    # 存储
    storage_backend: str = "local"  # local | s3
    local_storage_dir: str = "./data/storage"
    s3_endpoint: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket: str = "prism"

    # Agent
    prism_agent_model: str = "openai:gpt-4o-mini"
    openai_api_key: str | None = None
    agent_demo_mode: bool = True

    # CORS：逗号分隔
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        """解析 CORS 白名单。"""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """获取单例配置（进程内缓存）。"""
    return Settings()
