"""
Модуль загрузки и кэширования ML модели.
"""

from catboost import CatBoostRegressor
from functools import lru_cache


MODEL_PATH = "ml/models/latest_model.cbm"


@lru_cache()
def get_model() -> CatBoostRegressor:
    """
    Загружает и кэширует ML модель CatBoost.

    Returns:
        CatBoostRegressor: Загруженная модель.
    """
    model = CatBoostRegressor()
    model.load_model(MODEL_PATH)
    return model
