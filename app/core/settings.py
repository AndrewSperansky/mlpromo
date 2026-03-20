# app/core/settings.py
"""
Application settings — централизованные конфигурации проекта.
"""


from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    ENV: str = "dev"  # dev / test / prod
    DEBUG: bool = True
    API_CONTRACT_VERSION: str = Field(
        default="ml-predict.v1",
        description="ML API contract version"
    )
    LOG_LEVEL: str = "INFO"

    # ===== ML FILE CONTRACT =====
    ML_MODEL_DIR: str = "/app/models/current"
    ML_META_PATH: str = "/app/models/current/cb_promo_v1.meta.json"
    # ============================

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/promo"
    REDIS_URL: str = "redis://localhost:6379/0"
    SQLALCHEMY_ECHO: bool = Field(default=False, alias="SQLALCHEMY_ECHO")

    # === Promote Governance ===
    PROMOTE_METRIC: str = "accuracy"  # или "rmse"
    PROMOTE_MIN_IMPROVEMENT_PERCENT: float = 0.0  # минимальное улучшение в %
    PROMOTE_REQUIRE_METRICS: bool = True  # требовать ли метрики

    class Config:
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
