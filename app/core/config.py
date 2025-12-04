# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/promo"
    REDIS_URL: str = "redis://localhost:6379/0"
    MODEL_STORE_PATH: str = "data/models_history"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
