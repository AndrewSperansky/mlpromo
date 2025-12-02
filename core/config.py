
import os
from pydantic_settings import BaseSettings

DATABASE_URL = os.getenv('DATABASE_URL','postgresql://promo:promo@db:5432/promoml')
MODEL_PATH = os.getenv('MODEL_PATH','app/ml/model_catboost.cbm')


class Settings(BaseSettings):
    ENV: str = "dev"
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"

    MODEL_PATH: str = "./ml/model.pkl"

    class Config:
        env_file = ".env"

settings = Settings()
