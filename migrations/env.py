from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from db.base import Base

# 🔴 ВАЖНО: импорт моделей
from models import ml_model, prediction, promo_positions  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
