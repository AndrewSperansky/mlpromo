"""
ML Prediction Service — выполнение предсказания.
"""

from typing import Dict, Any
from app.services.ml_model_loader import get_model


class MLPredictionService:
    """
    Выполняет предсказание модели и логирование ML-инференса.
    """

    def predict(self, data: Dict) -> Dict:
        """
        Выполняет инференс ML модели.

        Args:
            data (dict): Входные данные для модели.

        Returns:
            dict: Предсказание и метаинформация.
        """

        model = get_model()

        prediction = model.predict([list(data.values())])[0]

        return {
            "prediction": prediction,
            "model_version": "latest",
        }
