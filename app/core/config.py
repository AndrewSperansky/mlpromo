# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    database_url: str
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid",
        populate_by_name=True,
    )

settings = Settings()

