# app/services/ml_prediction_service.py

import numpy as np
import shap
import logging
import time
from typing import Dict, List, Any
from datetime import datetime, date, timezone
from app.ml.model_loader import ModelLoader
from app.ml.runtime_state import ML_RUNTIME_STATE



logger = logging.getLogger("promo_ml")


class MLPredictionService:
    """
    Сервис ML-предсказаний и SHAP-объяснений.
    Работает с ПЛОСКИМИ признаками (НЕ dict features).
    """

    def __init__(self):
        """
        Загружает модель и метаданные.
        """
        model, meta = ModelLoader.load()

        loaded = ModelLoader.load()
        self.model = loaded["model"]
        self.meta = loaded["meta"]

        if not isinstance(meta, dict):
            meta = {}

        self.model = model
        self.meta: Dict[str, Any] = meta
        self.feature_order: List[str] = meta.get("feature_order", [])

        self.model_id: str = meta.get("model_id", "unknown")
        self.version: str = meta.get("version", "dev")
        self.trained_at: datetime = meta.get(
            "trained_at", datetime.now(timezone.utc)
        )

        self.explainer = (
            shap.TreeExplainer(self.model) if self.model is not None else None
        )

        # Временная отладка — удалите после диагностики!
        print(f"Type of model: {type(self.model)}")
        print(f"Model: {self.model}")
        print(f"[DEBUG] Тип model: {type(self.model)}")
        print(f"[DEBUG] Значение model: {self.model}")
        print(f"[DEBUG] meta: {self.meta}")


    def _build_feature_vector(self, features: Dict[str, float]) -> np.ndarray:
        """
        Приводит входные features к порядку feature_order.
        """
        if self.feature_order:
            return np.array(
                [[features[f] for f in self.feature_order]],
                dtype=float,
            )

        return np.array([list(features.values())], dtype=float)

    def predict(
        self,
        *,
        prediction_date: date,
        price: float,
        discount: float,
        avg_sales_7d: float,
        promo_days_left: int,
        promo_code: str,
        sku: str,
    ) -> Dict:
        """
        Выполняет предсказание ML-модели + SHAP объяснение.
        """
        # ======== ML CONTRACT GUARD ========
        contract = ML_RUNTIME_STATE.get("contract", {})

        if contract.get("status") != "ok":
            logger.warning(
                "ML contract degraded — fallback used",
                extra={"contract": contract},
            )

            return {
                "promo_code": promo_code,
                "sku": sku,
                "date": prediction_date,
                "prediction": None,
                "baseline": None,
                "uplift": None,
                "shap": [],
                "model_id": self.model_id,
                "version": self.version,
                "trained_at": self.trained_at,
                "fallback_used": True,
                "reason": "ml_contract_degraded",
            }
        # ======== END CONTRACT GUARD ========



        features = {
            "price": price,
            "discount": discount,
            "avg_sales_7d": avg_sales_7d,
            "promo_days_left": promo_days_left,
        }

        logger.info("ML prediction started", extra=features)

        if self.model is None:
            logger.error("Model is not loaded, fallback used")

            return {
                "promo_code": promo_code,
                "sku": sku,
                "date": prediction_date,
                "prediction": None,
                "model_id": self.model_id,
                "version": self.version,
                "trained_at": self.trained_at,
                "features": features,
                "fallback_used": True,
            }

        # ---------- 1. Features ----------
        X = self._build_feature_vector(features)

        # ---------- 2. Predict ----------
        start = time.time()
        y_pred = float(self.model.predict(X)[0])
        duration = round(time.time() - start, 5)

        logger.info(
            "ML inference completed",
            extra={"prediction": y_pred, "duration": duration},
        )

        # ---------- 3. SHAP ----------
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
                    "SHAP failed",
                    extra={"error": str(exc)},
                )

        # ---------- 4. Response ----------
        return {
            "promo_code": promo_code,
            "sku": sku,
            "date": prediction_date,
            "prediction": y_pred,
            "model_id": self.model_id,
            "version": self.version,
            "trained_at": self.trained_at,
            "features": features,
            "fallback_used": False,
            "shap": shap_output,
        }


