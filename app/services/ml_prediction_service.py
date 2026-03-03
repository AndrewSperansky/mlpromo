#  app/services/ml_prediction_service.py


import logging
from typing import Dict, List, Any
from datetime import datetime, timezone
from app.api.v1.ml.schemas import PredictionRequest

import pandas as pd
import shap
from catboost import Pool

from app.ml.model_loader import ModelLoader
from app.ml.runtime_state import ML_RUNTIME_STATE

logger = logging.getLogger(__name__)


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

        # Определяем индексы категориальных признаков
        self.cat_features_indices = []
        for i, feat in enumerate(self.feature_order):
            if feat in ['promo_code', 'sku']:
                self.cat_features_indices.append(i)

        self.ml_model_id: str = self.meta.get("ml_model_id", "unknown")
        self.version: str = self.meta.get("version", "dev")
        self.trained_at: datetime = self.meta.get(
            "trained_at", datetime.now(timezone.utc)
        )

        self.explainer = None

        if self.model is None:
            logger.error("ML model is None")
            return

        if isinstance(self.model, str):
            logger.error(
                "ML model is string, not loaded model object",
                extra={"model_value": self.model},
            )
            return

        # Пытаемся инициализировать SHAP
        try:
            logger.info("Initializing SHAP TreeExplainer...")
            self.explainer = shap.TreeExplainer(self.model)
            logger.info("SHAP TreeExplainer initialized successfully")
        except Exception as exc:
            logger.error(
                "SHAP explainer initialization FAILED",
                extra={
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "model_type": type(self.model).__name__,
                },
                exc_info=True,
            )

        logger.info(
            "ML model loaded",
            extra={
                "ml_model_id": self.ml_model_id,
                "version": self.version,
                "features": self.feature_order,
                "cat_features_indices": self.cat_features_indices,
                "shap_available": self.explainer is not None,
            },
        )

    def _validate_features(self, features: Dict[str, Any]) -> None:
        """Проверяет наличие всех фич"""
        if not self.feature_order:
            return

        missing = set(self.feature_order) - set(features.keys())
        if missing:
            raise ValueError(f"Missing features: {sorted(missing)}")

        for name in self.feature_order:
            value = features.get(name)
            if value is None:
                raise ValueError(f"Feature '{name}' is None")

            # Для числовых признаков проверяем тип
            if name not in ['promo_code', 'sku']:
                if not isinstance(value, (int, float)):
                    raise TypeError(
                        f"Feature '{name}' must be numeric, got {type(value).__name__}"
                    )

    def normalize_external_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Дополняет отсутствующие свойства значениями по умолчанию.
        Используется ТОЛЬКО для внешних интеграций (1C).
        """

        if not self.feature_order:
            return features

        normalized = features.copy()

        missing = set(self.feature_order) - set(normalized.keys())

        if missing:
            logger.warning(
                "1C payload missing features. Auto-filling: %s",
                sorted(missing)
            )

        for name in self.feature_order:
            if name not in normalized:
                if name in ["promo_code", "sku"]:
                    normalized[name] = "unknown"
                else:
                    normalized[name] = 0.0

        return normalized


    def _build_feature_vector(self, features: Dict[str, Any]) -> Pool:
        """
        Создает Pool для CatBoost с правильными типами признаков.
        """
        if not self.feature_order:
            raise ValueError("feature_order is empty")

        # Собираем значения в правильном порядке
        values = []
        for f in self.feature_order:
            val = features[f]
            # Конвертируем числа в float, строки оставляем как есть
            if isinstance(val, (int, float)) and f not in ['promo_code', 'sku']:
                values.append(float(val))
            else:
                values.append(str(val) if val is not None else "")

        # Создаем DataFrame для Pool
        df = pd.DataFrame([values], columns=self.feature_order)

        # Создаем Pool с указанием категориальных признаков
        return Pool(
            data=df,
            cat_features=self.cat_features_indices,
            feature_names=self.feature_order
        )

    def predict_from_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Базовое ML-предсказание по словарю фич.
        """
        self._validate_features(features)
        pool = self._build_feature_vector(features)

        # Предсказание
        y_pred = float(self.model.predict(pool)[0])

        # SHAP - создаем отдельный числовой DataFrame
        shap_output: List[Dict[str, Any]] = []

        if self.explainer:
            try:
                # Создаем числовой DataFrame для SHAP
                shap_values_list = []
                for f in self.feature_order:
                    val = features[f]
                    if f in ['promo_code', 'sku'] and isinstance(val, str):
                        # Конвертируем строку в число для SHAP
                        shap_values_list.append(float(hash(val) % 10000))
                    else:
                        shap_values_list.append(float(val))

                df_shap = pd.DataFrame([shap_values_list], columns=self.feature_order)

                # Вычисляем SHAP values
                shap_values = self.explainer.shap_values(df_shap)

                # Обрабатываем результат
                if isinstance(shap_values, list):
                    # Для мульти-класса
                    values = shap_values[0][0]
                else:
                    # Для регрессии
                    values = shap_values[0]

                feature_names = self.feature_order or list(features.keys())
                shap_output = [
                    {"feature": f, "effect": float(values[i])}
                    for i, f in enumerate(feature_names)
                ]

                logger.debug("SHAP calculated successfully", extra={"shap_length": len(shap_output)})

            except Exception as exc:
                logger.warning(
                    "SHAP calculation failed",
                    extra={
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    },
                    exc_info=True,
                )

        return {
            "prediction": y_pred,
            "shap_values": shap_output,
            "features": features,
            "ml_model_id": self.ml_model_id,
            "version": self.version,
            "trained_at": self.trained_at,
        }

    def predict_raw(self, features: dict) -> tuple[float, dict]:
        """
        Низкоуровневое предсказание для 1С.
        """
        result = self.predict_from_features(features)
        return result["prediction"], result.get("shap_values", {})

    def predict(self, payload: PredictionRequest) -> Dict[str, Any]:
        """
        Выполняет предсказание ML-модели + SHAP объяснение.
        """
        contract = ML_RUNTIME_STATE.get("contract", {})

        logger.info(
            "ML API called",
            extra={
                "promo_code": payload.promo_code,
                "sku": payload.sku,
            },
        )

        if contract.get("status") != "ok":
            return self._fallback_response(payload, "ml_contract_degraded")

        # Формируем features со всеми полями
        features = {
            "price": payload.price,
            "discount": payload.discount,
            "avg_sales_7d": payload.avg_sales_7d,
            "avg_discount_7d": payload.avg_discount_7d,
            "promo_days_left": payload.promo_days_left,
            "promo_code": payload.promo_code,
            "sku": payload.sku,
        }

        logger.info("ML prediction started", extra=features)

        if self.model is None:
            return self._fallback_response(payload, "model_not_loaded", features)

        try:
            self._validate_features(features)
        except Exception as exc:
            logger.error(
                "Feature validation failed",
                extra={"error": str(exc), "features": features},
            )
            return self._fallback_response(payload, "feature_validation_failed", features)

        # СОЗДАЕМ ДАННЫЕ ДЛЯ МОДЕЛИ (СО СТРОКАМИ)
        values = []
        for f in self.feature_order:
            val = features[f]
            if isinstance(val, (int, float)) and f not in ['promo_code', 'sku']:
                values.append(float(val))
            else:
                values.append(str(val) if val is not None else "")

        df = pd.DataFrame([values], columns=self.feature_order)

        # СОЗДАЕМ POOL ДЛЯ PREDICT
        pool = Pool(
            data=df,
            cat_features=self.cat_features_indices,
            feature_names=self.feature_order
        )

        # ПРЕДСКАЗАНИЕ
        y_pred = float(self.model.predict(pool)[0])

        # СОЗДАЕМ ЧИСЛОВЫЕ ДАННЫЕ ДЛЯ SHAP (НЕ ИСПОЛЬЗУЕМ POOL!)
        shap_output = []
        if self.explainer:
            try:
                logger.debug("Starting SHAP calculation")

                # Создаем отдельный числовой DataFrame для SHAP
                shap_values_list = []
                for f in self.feature_order:
                    val = features[f]
                    if f in ['promo_code', 'sku']:
                        # Конвертируем строку в число для SHAP
                        if isinstance(val, str):
                            # Используем стабильное хеширование
                            shap_values_list.append(float(hash(val) % 10000))
                        else:
                            shap_values_list.append(float(val))
                    else:
                        shap_values_list.append(float(val))

                # Создаем DataFrame из одной строки
                df_shap = pd.DataFrame([shap_values_list], columns=self.feature_order)

                logger.debug(f"SHAP input shape: {df_shap.shape}")

                # Вычисляем SHAP values
                shap_values = self.explainer.shap_values(df_shap)

                # Обрабатываем результат
                if isinstance(shap_values, list):
                    # Для мульти-класса
                    values = shap_values[0][0]
                else:
                    # Для регрессии
                    values = shap_values[0]

                feature_names = self.feature_order or list(features.keys())
                shap_output = [
                    {"feature": f, "effect": float(values[i])}
                    for i, f in enumerate(feature_names)
                ]

                logger.info(
                    "SHAP calculated successfully",
                    extra={"shap_length": len(shap_output)}
                )

            except Exception as exc:
                logger.error(
                    "SHAP calculation failed",
                    extra={
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    },
                    exc_info=True,
                )
        else:
            logger.warning("SHAP explainer not available")

        return {
            "promo_code": payload.promo_code,
            "sku": payload.sku,
            "date": payload.prediction_date,
            "prediction": y_pred,
            "ml_model_id": self.ml_model_id,
            "version": self.version,
            "trained_at": self.trained_at,
            "features": features,
            "fallback_used": False,
            "shap": shap_output,
        }

    def _fallback_response(self, payload: PredictionRequest, reason: str, features: dict = None) -> Dict[str, Any]:
        """Унифицированный ответ при fallback"""
        return {
            "promo_code": payload.promo_code,
            "sku": payload.sku,
            "date": payload.prediction_date,
            "prediction": None,
            "ml_model_id": self.ml_model_id,
            "version": self.version,
            "trained_at": self.trained_at,
            "features": features or {},
            "shap": [],
            "fallback_used": True,
            "reason": reason,
        }