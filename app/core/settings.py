# app/core/settings.py
"""
Application settings — централизованные конфигурации проекта.
"""


from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    ENV: str = "dev"  # dev / prod
    DEBUG: bool = True
    VERSION: str = Field(default="dev", alias="VERSION")
    LOG_LEVEL: str = "INFO"

    # ===== ML FILE CONTRACT =====
    ML_MODEL_PATH: str = "/app/models/baseline_catboost.pkl"
    ML_META_PATH: str = "/app/models/baseline_catboost.meta.json"
    # ============================

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/promo"
    REDIS_URL: str = "redis://localhost:6379/0"
    SQLALCHEMY_ECHO: bool = Field(default=False, alias="SQLALCHEMY_ECHO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
