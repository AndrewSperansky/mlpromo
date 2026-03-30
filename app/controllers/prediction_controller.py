# app/controllers/prediction_controller.py

import json
import logging
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.ml.runtime_state import ML_RUNTIME_STATE
from app.services.ml_prediction_service import MLPredictionService
from app.schemas.prediction_schema import (
    PredictionRequest,
    PredictionResponse,
    ShapValue,
    FinanceMetrics,
    PromoEffectiveness,
    HistoricalContext,
)

from app.services.promo_calculator_service import PromoCalculatorService
from app.services.historical_data_service import HistoricalDataService

logger = logging.getLogger("promo_ml")


class PredictionController:

    def __init__(self, service: MLPredictionService, db: Session):
        self.service = service
        self.historical = HistoricalDataService(db)

    def predict(
            self,
            payload: PredictionRequest,
            db: Session,
    ) -> PredictionResponse:

        logger.info(f"🔥 Predict request payload: {payload}")

        # 1. Преобразуем payload в словарь фич (все поля, кроме promo_code, sku, prediction_date)
        features_dict = {
            "promo_id": payload.promo_code,           # ← promo_code → promo_id
            "sku": payload.sku,
            "store_id": payload.store_id,
            "promo_week1": payload.promo_week1,
            "promo_week2": payload.promo_week2,
            "regular_price": payload.regular_price,
            "promo_price": payload.promo_price,
            "prev_promo_id": payload.prev_promo_id or "",
            "adv_carrier": payload.adv_carrier or "",
            "adv_material": payload.adv_material or "",
            "promo_mechanics": payload.promo_mechanics or "",
        }

        # 2. ML предсказание
        prediction_result, shap_list = self.service.predict_raw(features_dict)

        if isinstance(prediction_result, float):
            prediction_result = {
                "prediction": prediction_result,
                "baseline": None,
                "uplift": None,
                "fallback_used": False,
                "reason": None,
            }

        shap_objs = [
            ShapValue(feature=s["feature"], effect=s["effect"])
            for s in shap_list
        ]

        # 3. Runtime meta
        model_id = ML_RUNTIME_STATE.get("ml_model_id")
        model_version = ML_RUNTIME_STATE.get("version")

        # ======================================================

        # 🔥 Получаем исторические данные из industrial_dataset_raw
        sku_history_data = self.historical.get_sku_history(
            sku=payload.sku,
            store_id=payload.store_id
        )

        # Создаём объект HistoricalContext
        historical_context = None
        if sku_history_data:
            historical_context = HistoricalContext(
                sku=sku_history_data.get("sku", payload.sku),
                store_id=sku_history_data.get("store_id"),
                total_records=sku_history_data.get("total_records", 0),
                avg_sales=sku_history_data.get("avg_week1_sales", 0),  # ← обновлено имя поля
                avg_regular_sales=sku_history_data.get("avg_regular_price", 0),  # placeholder
                avg_turnover=0,  # пока нет
                sales_volatility=sku_history_data.get("sales_volatility", 0),
                max_sales=0,  # пока нет
                min_sales=0,  # пока нет
                last_promo=sku_history_data.get("last_promo"),
                seasonal_patterns=None,
            )

        # 🔥 Рассчитываем baseline
        baseline = self.historical.calculate_baseline(
            sku=payload.sku,
            store_id=payload.store_id,
            date=payload.prediction_date.isoformat()
        )

        # 🔥 Рассчитываем uplift
        raw_prediction = prediction_result["prediction"]
        uplift_value = ((raw_prediction - baseline) / baseline * 100) if baseline > 0 else 0

        # 🔥 Анализируем эффективность промо (если есть)
        promo_effectiveness = None
        if payload.promo_code:
            promo_data = self.historical.get_promo_effectiveness(payload.promo_code)
            if promo_data:
                promo_effectiveness = PromoEffectiveness(
                    promo_id=promo_data.get("promo_id", payload.promo_code),
                    total_records=promo_data.get("total_records", 0),
                    total_sales=promo_data.get("total_sales", 0),
                    total_baseline=promo_data.get("total_baseline", 0),
                    avg_uplift=promo_data.get("avg_uplift", 0),
                    avg_discount=promo_data.get("avg_discount", 0),
                    effectiveness=promo_data.get("effectiveness", "unknown"),
                    message=promo_data.get("message", ""),
                )

        # 4. Формируем response
        response = PredictionResponse(
            promo_code=payload.promo_code,
            sku=payload.sku,
            store_id=payload.store_id,
            date=payload.prediction_date,
            prediction=raw_prediction,
            baseline=round(baseline, 2),
            uplift=round(uplift_value, 2),
            shap_values=shap_objs,
            ml_model_id=str(model_id),
            version=model_version,
            trained_at=ML_RUNTIME_STATE.get("trained_at"),
            features=features_dict,  # сохраняем для отладки
            fallback_used=prediction_result["fallback_used"],
            reason=prediction_result["reason"],
            promo_effectiveness=promo_effectiveness,
            historical_context=historical_context,
        )

        # 5. Audit log
        request_id = uuid4()
        features_json = json.dumps(features_dict, default=str)

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
                "prediction_value": raw_prediction,
                "features": features_json,
            }
        )

        # 6. Финансовые метрики (опционально)
        try:
            calculator_data = {
                "SKU": payload.sku,
                "BasePrice": payload.regular_price,
                "PromoPrice": payload.promo_price,
                "BaseSales": baseline or 0,
                "Elasticity": 0.5,
                "CostPerUnit": 0,
            }

            finance_result = PromoCalculatorService.compute_item(calculator_data)

            response.finance_metrics = FinanceMetrics(
                SKU=finance_result["SKU"],
                NewSales=round(finance_result["NewSales"]),
            )

            logger.info(f"💰 Finance metrics calculated: {response.finance_metrics}")

        except Exception as e:
            logger.warning(f"Financial calculation failed: {e}")
            response.finance_metrics = None

        db.commit()

        return response