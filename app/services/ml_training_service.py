"""
ML Training Service — обучение модели CatBoost.
"""

from typing import Dict, Any
from catboost import CatBoostRegressor
import logging

logger = logging.getLogger("promo_ml")


class MLTrainingService:
    """
    Сервис обучения ML модели.
    Заготовка для тренировки CatBoost модели.
    Релизим в этапах 7–10 ToDo.
    """

    def train(self, dataset: Any, config: Dict) -> str:
        """
        Выполняет обучение модели CatBoost.

        Args:
            dataset: Объект с данными для обучения.
            config (dict): Параметры модели.

        Returns:
            str: Путь к сохранённой модели.
        """
        logger.info("ML training started")

        model = CatBoostRegressor(**config)
        model.fit(dataset["X_train"], dataset["y_train"])

        model_path = "ml/models/latest_model.cbm"
        model.save_model(model_path)

        logger.info("ML training completed")

        return {"status": "training_stub", "model_path": model_path}
