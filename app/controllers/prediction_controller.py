# app/controllers/prediction_controller.py

import json
import logging
import time
import numpy as np
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Tuple

from app.ml.runtime_state import ML_RUNTIME_STATE
from app.services.ml_prediction_service import MLPredictionService
from app.schemas.prediction_schema import (
    PredictionRequest,
    PredictionResponse,
    ShapValue,
    HistoricalContext,
    BatchPredictionRequest,
    BatchPredictionResponse,
)
from app.services.promo_calculator_service import PromoCalculatorService
from app.services.historical_data_service import HistoricalDataService
from app.ml.feature_pipeline import FeaturePipeline
from app.ml.monitoring.inference_metrics import increment_errors_count, collect_inference_metrics  # ← добавить

logger = logging.getLogger("promo_ml")


class PredictionController:

    def __init__(self, service: MLPredictionService, db: Session):
        self.service = service
        self.historical = HistoricalDataService(db)
        self.feature_pipeline = FeaturePipeline()  # ← без db и redis

    def predict(
            self,
            payload: PredictionRequest,
            db: Session,
    ) -> PredictionResponse:
        start_time = time.time()

        try:

            logger.info(f"🔥 Predict request payload: {payload}")

            # =========================================================
            # 1. Получаем признаки SKU (с возможной подстановкой аналога)
            # =========================================================
            sku_data = self.historical.get_sku_features(payload.sku)

            logger.info(
                f"📦 SKU data: original={sku_data['original_sku']}, "
                f"effective={sku_data['effective_sku']}, "
                f"used_analog={sku_data['used_analog']}, "
                f"message={sku_data['message']}"
            )

            # =========================================================
            # 2. Формируем словарь фич для модели
            # =========================================================
            features_dict = {
                # 🔥 Промо-акция
                "promo_id": payload.promo_id or "Promo-#",

                # Временные параметры
                "week": payload.week,
                "month": payload.month,

                # SKU и категория
                "sku": sku_data["effective_sku"] or payload.sku,
                "category": sku_data["features"].get("category") or payload.category,

                # Цены
                "regular_price": payload.regular_price,
                "promo_price": payload.promo_price,

                # Магазин и локация
                "store_id": payload.store_id,
                "region": payload.region,
                "store_location_type": sku_data["features"].get("store_location_type") or payload.store_location_type,
                "format_assortment": sku_data["features"].get("format_assortment") or payload.format_assortment,

                # Маркетинг и механики
                "adv_carrier": payload.adv_carrier or "",
                "adv_material": payload.adv_material or "",
                "promo_mechanics": payload.promo_mechanics or "",
                "marketing_type": payload.marketing_type or "",

                # Справочные поля
                "analog_sku": sku_data["features"].get("analog_sku") or payload.analog_sku or [],
            }

            # 2.1 Трансформируем фичи (без БД)
            full_features = self.feature_pipeline.build_features(features_dict)

            # =========================================================
            # 3. ML предсказание
            # =========================================================
            prediction_result, shap_list = self.service.predict_raw(full_features)

            # Извлекаем k_uplift (коэффициент прироста)
            if isinstance(prediction_result, dict):
                k_uplift = float(prediction_result.get("prediction", 1.0))
            else:
                k_uplift = float(prediction_result) if prediction_result is not None else 1.0

            logger.info(f"🎯 Prediction result: k_uplift={k_uplift:.4f}")

            # =========================================================
            # 4. SHAP значения
            # =========================================================
            shap_objs = [
                ShapValue(feature=s["feature"], effect=s["effect"])
                for s in shap_list
            ]

            # =========================================================
            # 5. Runtime meta
            # =========================================================
            model_id = ML_RUNTIME_STATE.get("ml_model_id")
            model_version = ML_RUNTIME_STATE.get("version")

            # =========================================================
            # 6. Формируем исторический контекст
            # =========================================================
            historical_context = HistoricalContext(
                sku=payload.sku,
                store_id=payload.store_id,
                total_records=0,
                avg_sales=0,
                avg_regular_sales=0,
                avg_turnover=0,
                sales_volatility=0,
                max_sales=0,
                min_sales=0,
                last_promo=None,
                seasonal_patterns=None,
            )

            # 🔥 Вычисляем абсолютный прогноз в зависимости от baseline
            baseline_value = payload.baseline if payload.baseline is not None else 1.0
            absolute_prediction = k_uplift * baseline_value
            uplift_percent = (k_uplift - 1.0) * 100 if payload.baseline is None else ((k_uplift * baseline_value - baseline_value) / baseline_value) * 100

            # =========================================================
            # 7. Формируем ответ
            # =========================================================
            response = PredictionResponse(
                # Основные поля
                promo_id=payload.promo_id,
                sku=payload.sku,
                store_id=payload.store_id,

                # Категориальные поля (для контекста)
                category=payload.category,
                region=payload.region,
                store_location_type=payload.store_location_type,
                format_assortment=payload.format_assortment,

                # Входные параметры (для контекста)
                week=payload.week,
                month=payload.month,
                regular_price=payload.regular_price,
                promo_price=payload.promo_price,
                marketing_type=payload.marketing_type,

                # Результат прогноза
                k_uplift=round(k_uplift, 4),
                baseline=baseline_value,
                prediction_absolute=round(absolute_prediction, 2),
                uplift_percent=round(uplift_percent, 2),
                confidence=None,

                # SHAP
                shap_values=shap_objs,

                # Метаданные модели
                ml_model_id=str(model_id),
                version=model_version,
                trained_at=ML_RUNTIME_STATE.get("trained_at"),

                # Дополнительная информация
                features_used=features_dict,
                fallback_used=sku_data["used_analog"],
                reason=sku_data["message"] if sku_data["used_analog"] else None,

                # Исторический контекст
                historical_context=historical_context,

            )

            logger.info(f"✅ Response created successfully")

            # =========================================================
            # 8. Audit log
            # =========================================================
            request_id = uuid4()
            features_json = json.dumps({
                "request": payload.model_dump(),
                "features_used": features_dict,
                "sku_data": {
                    "original_sku": sku_data["original_sku"],
                    "effective_sku": sku_data["effective_sku"],
                    "used_analog": sku_data["used_analog"],
                    "message": sku_data["message"]
                }
            }, default=str)

            db.execute(
                text("""
                           INSERT INTO ml_prediction_audit
                           (
                               request_id,
                               model_id,
                               model_version,
                               prediction_value,
                               features
                           )
                           VALUES
                           (
                               :request_id,
                               :model_id,
                               :model_version,
                               :prediction_value,
                               CAST(:features AS JSONB)
                           )
                       """),
                {
                    "request_id": request_id,
                    "model_id": model_id,
                    "model_version": model_version,
                    "prediction_value": k_uplift,
                    "features": features_json,
                }
            )

            # =========================================================
            # 9. Финансовые метрики (опционально)
            # =========================================================
            # try:
            #     calculator_data = {
            #         "SKU": payload.sku,
            #         "BasePrice": payload.regular_price,
            #         "PromoPrice": payload.promo_price,
            #         "BaseSales": 0,
            #         "KUplift": k_uplift,
            #         "Elasticity": 0.5,
            #         "CostPerUnit": 0,
            #     }
            #
            #     finance_result = PromoCalculatorService.compute_item(calculator_data)
            #
            #     response.finance_metrics = FinanceMetrics(
            #         SKU=finance_result["SKU"],
            #         NewSales=round(finance_result.get("predicted_sales", 0)),
            #     )
            #
            #     logger.info(f"💰 Finance metrics calculated: {response.finance_metrics}")
            #
            # except Exception as e:
            #     logger.warning(f"Financial calculation failed: {e}")
            #     response.finance_metrics = None
            # ==================================================================================

            db.commit()

            # =========================================================
            # 10. Latency и метрики (НОВОЕ)
            # =========================================================
            latency_ms = (time.time() - start_time) * 1000
            logger.info(f"⏱️ Prediction latency: {latency_ms:.2f} ms")

            # Собираем метрики инференса
            try:
                # Подготавливаем числовые фичи для метрик
                feature_values = list(features_dict.values())
                numeric_features = []
                for v in feature_values:
                    if isinstance(v, (int, float)):
                        numeric_features.append(float(v))
                    elif isinstance(v, str):
                        numeric_features.append(float(hash(v) % 10000))
                    else:
                        numeric_features.append(0.0)

                collect_inference_metrics(
                    ml_model_id=str(model_id),
                    inputs=np.array([numeric_features]),
                    outputs=np.array([k_uplift]),
                    latency_ms=latency_ms
                )
            except Exception as e:
                logger.warning(f"Failed to collect inference metrics: {e}")

            return response

        except Exception as e:
            # 🔥 УВЕЛИЧИВАЕМ СЧЁТЧИК ОШИБОК
            increment_errors_count()
            logger.error(f"Prediction failed: {e}", exc_info=True)
            raise






    def predict_batch(
            self,
            payload: BatchPredictionRequest,
            db: Session,
    ) -> BatchPredictionResponse:
        """
        Batch предсказание — обрабатывает список запросов
        """
        logger.info(f"🔥 Batch predict request: {len(payload.requests)} items")

        results = []
        success_count = 0
        error_count = 0

        for idx, req in enumerate(payload.requests):
            try:
                logger.debug(f"Processing request {idx + 1}/{len(payload.requests)}")
                result = self.predict(req, db)
                results.append(result)
                success_count += 1
            except Exception as e:
                logger.error(f"Batch prediction error at index {idx}: {e}")
                # Возвращаем fallback для ошибочного запроса
                results.append(self._create_fallback_response(req, str(e)))
                error_count += 1

        return BatchPredictionResponse(
            predictions=results,
            total_count=len(payload.requests),
            success_count=success_count,
            error_count=error_count,
        )


    def _create_fallback_response(self, req: PredictionRequest, error_msg: str) -> PredictionResponse:
        """Создаёт fallback ответ при ошибке"""
        return PredictionResponse(
            promo_id=req.promo_id,
            sku=req.sku,
            store_id=req.store_id,
            category=req.category,
            region=req.region,
            store_location_type=req.store_location_type,
            format_assortment=req.format_assortment,
            week=req.week,
            month=req.month,
            regular_price=req.regular_price,
            promo_price=req.promo_price,
            marketing_type=req.marketing_type,
            k_uplift=1.0,
            confidence=None,
            shap_values=[],
            ml_model_id="unknown",
            version="unknown",
            trained_at=None,
            features_used=None,
            fallback_used=True,
            reason=error_msg,
            historical_context=None,
            prediction=1.0,
            baseline=1.0,
            uplift=0.0,
        )