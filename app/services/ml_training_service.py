"""
ML Training Service — обучение модели CatBoost.
"""

from typing import Dict, Any
from catboost import CatBoostRegressor


class MLTrainingService:
    """
    Сервис обучения ML модели.
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

        model = CatBoostRegressor(**config)
        model.fit(dataset["X_train"], dataset["y_train"])

        model_path = "ml/models/latest_model.cbm"
        model.save_model(model_path)

        return model_path
