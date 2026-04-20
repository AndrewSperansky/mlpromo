# app/core/settings.py
"""
Application settings — централизованные конфигурации проекта.
"""


from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    ENV: str = "prod"  # dev / test / prod
    DEBUG: bool = False
    API_CONTRACT_VERSION: str = Field(
        default="ml-predict.v1",
        description="ML API contract version"
    )
    LOG_LEVEL: str = "INFO"

    # ===== ML FILE CONTRACT =====

    ML_MODEL_DIR: str = "/app/models"   # Используем только в model_loader.py!

    ML_CURRENT_DIR: str = "/app/models/current"
    ML_CANDIDATE_DIR: str = "/app/models/candidate"
    ML_LINEAGE_DIR: str = "/app/models/history"
    ML_METRICS_DIR: str = "/app/models/metrics"
    ML_ARCHIVE_DIR: str = "/app/models/archive"

    ML_META_PATH: str = "/app/models/current/cb_promo_v1.meta.json"


    # ===== DATABASE =============
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/promo"
    REDIS_URL: str = "redis://localhost:6379/0"
    SQLALCHEMY_ECHO: bool = Field(default=False, alias="SQLALCHEMY_ECHO")

    # === Promote Governance ===
    PROMOTE_METRIC: str = "accuracy"  # или "rmse"
    PROMOTE_MIN_IMPROVEMENT_PERCENT: float = 0.01  # минимальное улучшение в %
    PROMOTE_REQUIRE_METRICS: bool = True  # требовать ли метрики

    # JWT Settings
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 часа

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
