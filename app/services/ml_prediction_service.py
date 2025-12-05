import logging
import time
from typing import Dict, List, Any

import numpy as np
import shap

from app.ml.model_loader import ModelLoader

logger = logging.getLogger("promo_ml")


class MLPredictionService:
    """
    Сервис ML-предсказаний и SHAP-объяснений.
    """

    def __init__(self):
        """
        Загружает модель и метаданные.
        """
        model, meta = ModelLoader.load()

        # Явно задаем тип meta, чтобы Pylint не ругался
        if not isinstance(meta, dict):
            meta = {}

        self.model = model
        self.meta: Dict[str, Any] = meta
        self.feature_order: List[str] = meta.get("feature_order", [])

        # Инициализируем SHAP
        self.explainer = (
            shap.TreeExplainer(self.model) if self.model is not None else None
        )

    def _build_feature_vector(self, features: Dict[str, float]) -> np.ndarray:
        """
        Приводит входные features к порядку feature_order.
        Если порядок не задан — просто используем values().
        """
        if self.feature_order:
            try:
                return np.array(
                    [[features[f] for f in self.feature_order]], dtype=float
                )
            except KeyError as missing:
                logger.error(
                    "Missing feature for ML inference",
                    extra={"missing_feature": str(missing)},
                )
                raise
        else:
            return np.array([list(features.values())], dtype=float)

    def predict(self, features: Dict) -> Dict:
        """
        Выполняет предсказание ML-модели + SHAP объяснение.
        """

        logger.info("ML prediction started", extra={"features": features})

        if self.model is None:
            logger.error("Prediction requested but model is not loaded")
            return {
                "prediction": None,
                "baseline": None,
                "uplift": None,
                "shap": [],
            }

        # -------- 1. Формирование X ----------
        X = self._build_feature_vector(features)

        # -------- 2. Предсказание ----------
        start = time.time()
        y_pred = float(self.model.predict(X)[0])
        duration = round(time.time() - start, 5)

        logger.info(
            "ML inference completed",
            extra={"prediction": y_pred, "duration_sec": duration},
        )

        # -------- 3. SHAP объяснения ----------
        shap_output = []
        if self.explainer:
            try:
                shap_values = self.explainer.shap_values(X)[0]
                feature_names = self.feature_order or list(features.keys())
                shap_output = [
                    {"feature": f, "effect": float(v)}
                    for f, v in zip(feature_names, shap_values)
                ]
            except Exception as exc:
                logger.warning(
                    "SHAP calculation failed",
                    extra={"error": str(exc)},
                )

        # -------- 4. Ответ ----------
        return {
            "prediction": y_pred,
            "baseline": y_pred * 0.85,
            "uplift": y_pred * 0.15,
            "duration": duration,
            "shap": shap_output,
        }
