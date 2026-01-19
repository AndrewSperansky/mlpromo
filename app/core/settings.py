# app/core/settings.py
"""
Application settings — централизованные конфигурации проекта.
"""


from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    ENV: str = "dev"  # dev / prod
    VERSION: str = Field(default="dev", alias="VERSION")
    DEBUG: bool = True

    MODEL_PATH: str = "/app/models/baseline_catboost.pkl"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "postgres://postgres:postgres@postgres:5432/promo"
    REDIS_URL: str = "redis://localhost:6379/0"
    SQLALCHEMY_ECHO: bool = Field(default=False, alias="SQLALCHEMY_ECHO")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        populate_by_name=True,
    )


settings = Settings()
