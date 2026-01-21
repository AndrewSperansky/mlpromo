# app/services/ml_prediction_service.py

import logging
import time
from typing import Dict, List, Any
from datetime import datetime, date, timezone
from app.api.v1.ml.schemas import PredictionRequest  # Импорт Pydantic-модели
from app.core.settings import settings

import numpy as np
import shap

from app.ml.model_loader import ModelLoader
from app.ml.runtime_state import ML_RUNTIME_STATE

logger = logging.getLogger("promo_ml")


class MLPredictionService:
    """
    Сервис ML-предсказаний и SHAP-объяснений.
    """

    def __init__(self) -> None:
        """
        Загружает модель и метаданные.
        """
        loaded = ModelLoader.load()

        self.model = loaded.get("model")
        self.meta: Dict[str, Any] = loaded.get("meta", {}) or {}

        self.feature_order: List[str] = self.meta.get("feature_order", [])

        self.model_id: str = self.meta.get("model_id", "unknown")
        self.version: str = self.meta.get("version", "dev")
        self.trained_at: datetime = self.meta.get(
            "trained_at", datetime.now(timezone.utc)
        )

        self.explainer = None

        if self.model is None:
            logger.error("ML model is None")

        elif isinstance(self.model, str):
            logger.error(
                "ML model is string, not loaded model object",
                extra={"model_value": self.model},
            )

        else:
            try:
                self.explainer = shap.TreeExplainer(self.model)
            except Exception as exc:
                logger.warning(
                    "SHAP explainer initialization failed",
                    extra={"error": str(exc)},
                )

        logger.info(
            "ML model loaded",
            extra={
                "model_id": self.model_id,
                "version": self.version,
                "features": self.feature_order,
            },
        )

    def _validate_features(self, features: Dict[str, Any]) -> None:
        if not self.feature_order:
            return           # нет контракта — нечего валидировать

        missing = set(self.feature_order) - set(features.keys())
        if missing:
            raise ValueError(f"Missing features: {sorted(missing)}")

        for name in self.feature_order:
            value = features.get(name)
            if value is None:
                raise ValueError(f"Feature '{name}' is None")

            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"Feature '{name}' must be numeric, got {type(value).__name__}"
                )


    def _build_feature_vector(self, features: Dict[str, float]) -> np.ndarray:
        """
        Приводит входные features к порядку feature_order.
        """
        if self.feature_order:
            try:
                values = [features[f] for f in self.feature_order]
            except KeyError as exc:
                raise ValueError(
                    f"Missing feature for model: {exc}"
                ) from exc

            return np.array([values], dtype=float)

        return np.array([list(features.values())], dtype=float)



    def predict(self, payload: PredictionRequest) -> Dict[str, Any]:
        """
        Выполняет предсказание ML-модели + SHAP объяснение.
        """

        # ======== ML CONTRACT DEGRADED GUARD ========
        contract = ML_RUNTIME_STATE.get("contract", {})

        logger.info(
            "ML API called",
            extra={
                "contract": settings.API_CONTRACT_VERSION,
                "promo_code": payload.promo_code,
                "sku": payload.sku,
            },
        )

        if contract.get("status") != "ok":
            logger.warning(
                "ML contract degraded — fallback used",
                extra={"contract": contract},
            )

            return {
                "promo_code": payload.promo_code,
                "sku": payload.sku,
                "date": payload.prediction_date,
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
        # ======== END CONTRACT DEGRADED GUARD ========

        features = {
            "price": payload.price,
            "discount": payload.discount,
            "avg_sales_7d": payload.avg_sales_7d,
            "promo_days_left": payload.promo_days_left,
        }

        logger.info("ML prediction started", extra=features)

        # ======== FALLBACK ========

        if self.model is None:
            logger.error("Model is not loaded, fallback used")

            return {
                "promo_code": payload.promo_code,
                "sku": payload.sku,
                "date": payload.prediction_date,
                "prediction": None,
                "model_id": self.model_id,
                "version": self.version,
                "trained_at": self.trained_at,
                "features": features,
                "fallback_used": True,
                "reason": "model_not_loaded",
            }

        # ---------- 1. Feature validation ----------
        try:
            self._validate_features(features)
        except Exception as exc:
            logger.error(
                "Feature validation failed",
                extra={
                    "error": str(exc),
                    "features": features,
                },
            )

            return {
                "promo_code": payload.promo_code,
                "sku": payload.sku,
                "date": payload.prediction_date,
                "prediction": None,
                "baseline": None,
                "uplift": None,
                "model_id": self.model_id,
                "version": self.version,
                "trained_at": self.trained_at,
                "features": features,
                "fallback_used": True,
                "reason": "feature_validation_failed",
            }

        # ---------- 2. Build feature vector ----------
        X = self._build_feature_vector(features)

        # ---------- 3. Predict ----------
        start = time.time()
        y_pred = float(self.model.predict(X)[0])
        duration = round(time.time() - start, 5)

        logger.info(
            "ML inference completed",
            extra={
                "prediction": y_pred,
                "duration": duration,
            },
        )

        # ---------- 4. SHAP ----------
        shap_output: List[Dict[str, float]] = []

        if self.explainer:
            try:
                shap_values = self.explainer.shap_values(X)

                # CatBoost / sklearn compatibility
                values = (
                    shap_values[0]
                    if isinstance(shap_values, list)
                    else shap_values[0]
                )

                feature_names = self.feature_order or list(features.keys())

                shap_output = [
                    {"feature": f, "effect": float(v)}
                    for f, v in zip(feature_names, values)
                ]

            except Exception as exc:
                logger.warning(
                    "SHAP calculation failed",
                    extra={"error": str(exc)},
                )

        # ---------- 5. Response ----------
        return {
            "promo_code": payload.promo_code,
            "sku": payload.sku,
            "date": payload.prediction_date,
            "prediction": y_pred,
            "model_id": self.model_id,
            "version": self.version,
            "trained_at": self.trained_at,
            "features": features,
            "fallback_used": False,
            "shap": shap_output,
        }
