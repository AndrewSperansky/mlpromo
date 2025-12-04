"""
Application settings — централизованные конфигурации проекта.
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "dev"  # dev / prod
    DEBUG: bool = True

    MODEL_PATH: str = "ml/models/latest_model.cbm"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/promo"
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
