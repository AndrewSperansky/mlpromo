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
)

logger = logging.getLogger(__name__)


class PredictionController:

    def __init__(self, service: MLPredictionService):
        self.service = service

    def predict(
        self,
        payload: PredictionRequest,
        db: Session,
    ) -> PredictionResponse:

        logger.info(f"🔥 Predict request payload: {payload}")

        # 1. ML предсказание
        prediction_result, shap_list = self.service.predict_raw(payload.features)

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

        # 2. Runtime meta
        model_id = ML_RUNTIME_STATE.get("ml_model_id")
        model_version = ML_RUNTIME_STATE.get("version")

        # 3. Формируем response
        response = PredictionResponse(
            promo_code=payload.promo_code,
            sku=payload.sku,
            date=payload.prediction_date,
            prediction=prediction_result["prediction"],
            baseline=prediction_result["baseline"],
            uplift=prediction_result["uplift"],
            shap_values=shap_objs,
            ml_model_id=str(model_id),
            version=model_version,
            trained_at=ML_RUNTIME_STATE.get("trained_at"),
            features=payload.features,
            fallback_used=prediction_result["fallback_used"],
            reason=prediction_result["reason"],
        )

        # 4. Audit log
        request_id = uuid4()

        features_json = json.dumps(payload.model_dump(), default=str)

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
                "prediction_value": prediction_result["prediction"],
                "features": features_json,
            }
        )

        db.commit()

        return response