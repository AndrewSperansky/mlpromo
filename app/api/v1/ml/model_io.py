# api/v1/ml/model_io.py

from typing import Any
from app.core.settings import settings


def load_model() -> Any:
    """
    Заглушка загрузки модели.
    Позже: pickle / joblib / catboost
    """
    return {
        "ml_model_id": "dummy-model",
        "version": settings.VERSION,
    }
