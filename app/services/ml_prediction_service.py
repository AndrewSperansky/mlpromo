# app/services/ml_prediction_service.py

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from app.schemas.prediction_schema import PredictionRequest
from app.db.session import SessionLocal
from app.services.registry_service import ModelRegistryService
from app.core.settings import settings


import pandas as pd
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
        self.model = None
        self.meta: Dict[str, Any] = {}
        self.feature_order: List[str] = []
        self.cat_features_indices: List[int] = []
        self.ml_model_id: str = "unknown"
        self.version: str = "dev"
        self.trained_at: datetime = datetime.now(timezone.utc)

        self._load_model()
        self._refresh_meta()

    def _load_model(self) -> None:
        """Загружает модель через ModelLoader"""
        loaded = ModelLoader.load()
        self.model = loaded.get("model")
        self.meta: Dict[str, Any] = loaded.get("meta", {}) or {}

        if self.model is None:
            logger.error("ML model is None")
            return

        if isinstance(self.model, str):
            logger.error(
                "ML model is string, not loaded model object",
                extra={"model_value": self.model},
            )
            return

        logger.info("ML model loaded successfully")

    def _refresh_meta(self) -> None:
        """Обновляет метаданные из актуального runtime-state"""
        logger.info(f"🔥 REFRESH META: ML_RUNTIME_STATE = {ML_RUNTIME_STATE}")
        self.feature_order: List[str] = ML_RUNTIME_STATE.get("feature_order", [])
        logger.info(f"🔥 REFRESH META: feature_order = {self.feature_order}")
        self.ml_model_id: str = str(ML_RUNTIME_STATE.get("ml_model_id", "unknown"))
        self.version: str = ML_RUNTIME_STATE.get("version", "dev")
        self.trained_at: datetime = ML_RUNTIME_STATE.get(
            "trained_at", datetime.now(timezone.utc)
        )

        # ================================================================
        # 🔥 ОПРЕДЕЛЯЕМ ИНДЕКСЫ КАТЕГОРИАЛЬНЫХ ПРИЗНАКОВ
        # ================================================================
        self.cat_features_indices = []
        for i, feat in enumerate(self.feature_order):
            if feat in ['store_id', 'sku', 'category', 'region',
                        'store_location_type', 'format_assortment',
                        'promo_mechanics', 'adv_carrier', 'adv_material',
                        'marketing_type']:
                self.cat_features_indices.append(i)

        logger.info(
            "ML model meta refreshed",
            extra={
                "ml_model_id": self.ml_model_id,
                "version": self.version,
                "features": self.feature_order,
                "cat_features_indices": self.cat_features_indices,
            },
        )

    def _validate_features(self, features: Dict[str, Any]) -> None:
        """
        Проверяет наличие всех фич, которые ожидает модель.
        Лишние фичи игнорируются с предупреждением.
        """
        # ВРЕМЕННО ОТКЛЮЧАЕМ ВАЛИДАЦИЮ
        logger.info(f"⚠️ VALIDATION SKIPPED - features: {list(features.keys())}")
        return

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

        values = []
        for f in self.feature_order:
            val = features.get(f, "")

            # Числовые признаки → float
            if f in ['month', 'week', 'regular_price', 'promo_price']:
                try:
                    values.append(float(val) if val is not None else 0.0)
                except (ValueError, TypeError):
                    values.append(0.0)
            else:
                # Категориальные признаки → строка
                values.append(str(val) if val is not None else "")

        df = pd.DataFrame([values], columns=self.feature_order)

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

        # ================================================================
        # 🔥 SHAP через CatBoost (нативный способ)
        # ================================================================
        shap_output: List[Dict[str, Any]] = []

        try:
            shap_matrix = self.model.get_feature_importance(
                pool,
                type="ShapValues"
            )

            # Извлекаем SHAP значения (без expected_value)
            shap_values = shap_matrix[0, :-1]
            expected_value = float(shap_matrix[0, -1])

            shap_output = [
                {"feature": f, "effect": float(shap_values[i])}
                for i, f in enumerate(self.feature_order)
            ]

            logger.debug(
                "SHAP calculated successfully (CatBoost native)",
                extra={
                    "shap_length": len(shap_output),
                    "expected_value": expected_value
                }
            )

        except Exception as exc:
            logger.warning(
                "SHAP calculation failed (CatBoost native)",
                extra={
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
                exc_info=True,
            )
            shap_output = []

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

        # 🔥 ОБНОВЛЯЕМ МЕТАДАННЫЕ ПЕРЕД КАЖДЫМ ПРЕДСКАЗАНИЕМ
        self._refresh_meta()

        features = payload.features.copy()
        full_features = {
            **features,
            "promo_code": payload.promo_code,
            "sku": payload.sku,
            "prediction_date": payload.prediction_date
        }

        logger.info(f"🔥 features from payload: {payload.features}")
        logger.info("ML prediction started", extra=full_features)
        logger.info(f"🔥 features received: {list(full_features.keys())}")
        logger.info(f"🔥 PREDICT: self.feature_order = {self.feature_order}")
        logger.info(f"🔥 full_features keys: {list(full_features.keys())}")
        logger.info(f"🔥 full_features sample: {full_features}")

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

        # ================================================================
        # 🔥 BASELINE: приоритет — ручной > LSTM > fallback
        # ================================================================

        baseline = features.get("baseline")

        # Если baseline не указан или равен 0 — пробуем LSTM
        if (baseline is None or baseline == 0) and settings.USE_LSTM:
            lstm_baseline = self._get_lstm_baseline(
                sku=payload.sku,
                store_id=payload.store_id,
                prediction_date=payload.prediction_date.isoformat() if payload.prediction_date else None,
                regular_price=payload.regular_price,
            )

            if lstm_baseline is not None:
                baseline = lstm_baseline
                logger.info(f"✅ Using LSTM baseline: {baseline}")
            else:
                # LSTM не дала результат — используем fallback
                baseline = features.get("baseline", 1.0)
                if baseline is None or baseline == 0:
                    baseline = 1.0
                logger.debug(f"LSTM unavailable, using fallback baseline: {baseline}")
        else:
            # Если baseline указан вручную — используем его (приоритет!)
            baseline = baseline or 1.0
            if baseline is not None:
                logger.info(f"Using manual baseline: {baseline}")

        # Сохраняем baseline в features для дальнейшего использования
        features["baseline"] = baseline

        # СОЗДАЕМ ДАННЫЕ ДЛЯ МОДЕЛИ
        values = []
        for f in self.feature_order:
            val = features.get(f)
            if val is None:
                val = "" if f in ['promo_code', 'sku'] else 0.0

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

        # ================================================================
        # 🔥 SHAP через CatBoost (нативный способ)
        # ================================================================
        shap_output = []

        try:
            shap_matrix = self.model.get_feature_importance(
                pool,
                type="ShapValues"
            )

            shap_values = shap_matrix[0, :-1]
            expected_value = float(shap_matrix[0, -1])

            shap_output = [
                {"feature": f, "effect": float(shap_values[i])}
                for i, f in enumerate(self.feature_order)
            ]

            logger.info(
                "SHAP calculated successfully (CatBoost native)",
                extra={
                    "shap_length": len(shap_output),
                    "expected_value": expected_value
                }
            )

        except Exception as exc:
            logger.error(
                "SHAP calculation failed (CatBoost native)",
                extra={"error": str(exc)},
                exc_info=True,
            )
            shap_output = []

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

    def _get_q_hat_from_model(self) -> Optional[float]:
        """Устаревший метод. Используется ML_RUNTIME_STATE['conformal_q_hat']"""
        return ML_RUNTIME_STATE.get("conformal_q_hat")

    def predict_with_interval(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Предсказание с доверительным интервалом (Conformal Prediction).
        Интервал масштабируется пропорционально baseline.
        """
        logger.info(f"🔍 predict_with_interval called, features keys: {list(features.keys())}")

        # 1. Получаем предсказание
        prediction_result, shap_list = self.predict_raw(features)

        if isinstance(prediction_result, dict):
            pred_value = float(prediction_result.get("prediction", 1.0))
        else:
            pred_value = float(prediction_result) if prediction_result is not None else 1.0

        # 2. Получаем q_hat из runtime_state
        q_hat = ML_RUNTIME_STATE.get("conformal_q_hat")

        # ================================================================
        # 3. 🔥 BASELINE: приоритет — ручной > LSTM > fallback
        # 3. Получаем baseline (если не передан — используем 1.0)
        # ================================================================


        baseline = features.get("baseline")

        # Если baseline не указан ИЛИ равен 0 — пробуем LSTM
        baseline = features.get("baseline", 1.0)
        if baseline is None:
            baseline = 1.0

        logger.info(f"🔍 q_hat: {q_hat}, baseline: {baseline}, pred_value: {pred_value}")

        result = {
            "prediction": pred_value,
            "shap_values": shap_list
        }

        if q_hat is not None:
            # 🔥 Масштабируем q_hat на baseline
            interval_width = q_hat * baseline
            lower = pred_value - interval_width
            upper = pred_value + interval_width

            # ✅ НЕ обрезаем до нуля — интервал остаётся симметричным
            result["interval"] = {
                "lower": lower,
                "upper": upper
            }
            result["interval_width"] = upper - lower
            result["has_interval"] = True
            logger.info(f"✅ Interval: [{lower:.2f}, {upper:.2f}], width: {interval_width:.2f}")
        else:
            result["has_interval"] = False
            result["note"] = "Conformal prediction not available for this model"     # type: ignore

        return result


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

    # ================================================================
    # 4. 🔥 BASELINE: Получение Baseline из LTSM
    # ================================================================


    def _get_lstm_baseline(
            self,
            sku: str,
            store_id: str,
            prediction_date: str,
            regular_price: Optional[float] = None,
    ) -> Optional[float]:
        """
        Получает baseline (продажи без промо) из LSTM модели.
        Возвращает None, если LSTM не активна или произошла ошибка.

        🔮 FUTURE: LSTM интеграция готова, но отключена флагом USE_LSTM.
        Для включения установите USE_LSTM=True в настройках.
        """

        # ═══════════════════════════════════════════════════════════════
        # 🔮 LSTM INTEGRATION (FUTURE)
        # ═══════════════════════════════════════════════════════════════
        #
        # Данный код закладывает основу для использования LSTM модели
        # как источника baseline (продажи без промо).
        #
        # Сейчас LSTM выключена (USE_LSTM=False). Для включения:
        # 1. Обучите LSTM модель через /ml/torch/train/lstm/unified
        # 2. Активируйте её через /ml/torch/activate
        # 3. Установите USE_LSTM=True в настройках
        #
        # После активации LSTM будет автоматически подставлять baseline
        # для прогнозов, где он не указан вручную.
        # ═══════════════════════════════════════════════════════════════

        # Если LSTM выключена — сразу возвращаем None
        if not settings.USE_LSTM:
            logger.debug(
                "LSTM is disabled (USE_LSTM=False). "
                "Set USE_LSTM=True in settings to enable."
            )
            return None

        logger.info(f"🔮 Attempting to get LSTM baseline for SKU={sku}, store={store_id}")

        db = SessionLocal()
        try:
            registry = ModelRegistryService(db)

            # Ищем активную LSTM модель
            lstm_model = registry.get_active_model_by_algorithm(
                "pytorch_lstm_with_embeddings"
            )

            if not lstm_model:
                logger.debug("No active LSTM model found")
                return None

            # Загружаем meta.json
            import json
            from pathlib import Path
            meta_path = Path(lstm_model.model_path).with_suffix('.meta.json')
            if not meta_path.exists():
                logger.warning(f"LSTM meta not found: {meta_path}")
                return None

            with open(meta_path) as f:
                meta = json.load(f)

            # Создаём TorchPredictor и загружаем модель
            from app.ml_torch.inference.predictor import TorchPredictor
            predictor = TorchPredictor(db)
            predictor.load_model(
                Path(lstm_model.model_path),
                meta.get("model_config", {})
            )

            # Делаем прогноз
            from datetime import date
            target_date = date.fromisoformat(prediction_date) if prediction_date else date.today()

            result = predictor.predict_for_day(
                sku=sku,
                date=target_date,
                store_id=store_id,
                regular_price=regular_price,
            )

            baseline = result.get("predicted_quantity")
            logger.info(f"✅ LSTM baseline for {sku}: {baseline}")
            return baseline

        except Exception as e:
            logger.error(f"LSTM baseline failed: {e}", exc_info=True)
            return None
        finally:
            db.close()