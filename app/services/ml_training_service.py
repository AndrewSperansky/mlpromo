# app/services/ml_training_service.py

"""
ML Training Service — обучение модели CatBoost.
"""

from typing import Dict, Any
from catboost import CatBoostRegressor
import logging
from app.core.settings import settings
from pathlib import Path

logger = logging.getLogger("promo_ml")


class MLTrainingService:
    """
    Сервис обучения ML модели.
    Заготовка для тренировки CatBoost модели.
    Релиз в этапах 7–10 ToDo.
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

        model_path = Path(settings.ML_MODEL_PATH)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        # ВАЖНО: CatBoost сохраняем ТОЛЬКО в cbm
        model.save_model(
            str(model_path),
            format="cbm"
        )

        logger.info("ML training completed")
        logger.info("Model saved to %s", model_path)

        return str(model_path)
