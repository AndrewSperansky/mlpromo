"""
ML Prediction Service — выполнение предсказания.
"""

import logging
import time
from typing import Dict
import shap
import numpy as np
from app.services.ml_model_loader import get_model

logger = logging.getLogger("promo_ml")


class MLPredictionService:
    """
    Сервис ML-предсказаний + SHAP-объяснений.
    Выполняет предсказание модели и логирование ML-инференса.
    """

    def __init__(self, model):
        self.model = model
        self.explainer = shap.TreeExplainer(model) if model else None

    def predict(self, features: Dict) -> Dict:
        """
        Выполняет прогноз и SHAP-объяснение.
        Выполняет инференс ML модели + логирование.

        Args:
            data (dict): Входные данные для модели.

        Returns:
            dict: Предсказание и метаинформация.
        """

        logger.info("ML prediction started", extra={"features": features})

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

        if model:
            return {
                "prediction": prediction,
                "model_version": "latest",
                "duration": duration,
            }

        if not self.model:
            logger.warning("Prediction attempted without loaded model")
            return {
                "forecast_total": None,
                "baseline": None,
                "uplift": None,
                "shap": [],
            }

        try:
            X = np.array([list(features.values())], dtype=float)

            y_pred = float(self.model.predict(X)[0])

            # SHAP values
            shap_values = self.explainer.shap_values(X)[0] if self.explainer else []

            shap_output = [
                {"feature": name, "effect": float(value)}
                for name, value in zip(features.keys(), shap_values)
            ]

            ## Позднее обязательно уточнить
            logger.info("ML prediction completed")
            return {
                "forecast_total": y_pred,
                "baseline": y_pred * 0.85,  # базовая евристика (до ML)
                "uplift": y_pred * 0.15,
                "shap": shap_output,
            }

        except Exception as exc:
            logger.error("ML prediction error", extra={"error": str(exc)})
            raise
