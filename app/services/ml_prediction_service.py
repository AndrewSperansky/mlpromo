"""
ML Prediction Service — выполнение предсказания.
"""

import logging
import time
from typing import Dict
from app.services.ml_model_loader import get_model

logger = logging.getLogger("promo_ml")


class MLPredictionService:
    """
    Выполняет предсказание модели и логирование ML-инференса.
    """

    def predict(self, features: Dict) -> Dict:
        """
        Выполняет инференс ML модели + логирование.

        Args:
            data (dict): Входные данные для модели.

        Returns:
            dict: Предсказание и метаинформация.
        """

        model = get_model()
        start = time.time()

        logger.info(
            "ML inference started",
            extra={
                "input": features,
                "model_version": "latest",
            },
        )

        prediction = model.predict([list(features.values())])[0]
        duration = round(time.time() - start, 4)

        logger.info(
            "ML inference finished",
            extra={
                "prediction": prediction,
                "duration_sec": duration,
                "model_version": "latest",
            },
        )

        return {
            "prediction": prediction,
            "model_version": "latest",
            "duration": duration,
        }
