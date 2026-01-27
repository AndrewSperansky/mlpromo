# app/api/v1/ml/router.py

from uuid import UUID
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends
from sqlalchemy import text


from app.db.session import get_db
from app.ml.runtime_state import ML_RUNTIME_STATE
from app.services.ml_training_service import MLTrainingService
from app.services.ml_prediction_service import MLPredictionService

from app.api.v1.ml.schemas import (
    PredictionRequest,
    PredictionResponse,
    OneCPredictRequest,
    OneCPredictResponse,
)




router = APIRouter(tags=["ml-1c"])

# ========== DEPENDENCIES ==========


def get_prediction_service() -> MLPredictionService:
    """
    Возвращает сервис предсказаний.
    Модель загружается ВНУТРИ сервиса.
    """
    return MLPredictionService()


def get_training_service() -> MLTrainingService:
    return MLTrainingService()


# ========== ENDPOINTS ==========


@router.post(
    "/predict",
    summary="ML предсказание + SHAP",
    response_model=PredictionResponse,
)

def predict(
    payload: PredictionRequest,
    svc: MLPredictionService = Depends(get_prediction_service),
):
    """
    Выполняет ML-предсказание.

    PredictionRequest (вход):
    - prediction_date
    - price
    - discount
    - avg_sales_7d
    - promo_days_left
    - promo_code
    - sku
    """



    result = svc.predict(payload)


    return result


# @router.post("/train", summary="Обучение ML модели")
# def train_model(
#     dataset_path: str,
#     svc: MLTrainingService = Depends(get_training_service),
# ):
#     """
#     Запускает обучение ML модели.
#     """
    # return svc.train(dataset_path=dataset_path)
    # pass


@router.get("/dataset", summary="ML dataset (read-only)")
def get_ml_dataset(
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Читает витрину promo_ml_dataset_v1
    """
    query = text("""
        SELECT
            date,
            promo_code,
            sku,
            price,
            discount,
            target_sales_qty,
            avg_sales_7d,
            avg_discount_7d,
            promo_days_left
        FROM promo_ml_dataset_v1
        ORDER BY date, promo_code, sku
        LIMIT :limit
        OFFSET :offset
    """)

    rows = db.execute(
        query,
        {"limit": limit, "offset": offset},
    ).mappings().all()

    return {
        "count": len(rows),
        "items": rows,
    }


@router.get("/model-status")
def model_status():
    return {
        "checked": ML_RUNTIME_STATE["checked"],
        "status": ML_RUNTIME_STATE["status"],
        "model_loaded": ML_RUNTIME_STATE["model_loaded"],
        "model_id": ML_RUNTIME_STATE["model_id"],
        "version": ML_RUNTIME_STATE["version"],
        "checksum_verified": ML_RUNTIME_STATE["checksum_verified"],
        "errors": ML_RUNTIME_STATE.get("errors", []),
        "warnings": ML_RUNTIME_STATE.get("warnings", []),
    }


@router.post("/1c/predict", response_model=OneCPredictResponse)
def predict_from_1c(
    payload: OneCPredictRequest,
    db: Session = Depends(get_db),
    svc: MLPredictionService = Depends(),
):
    if not ML_RUNTIME_STATE.get("model_loaded"):
        raise HTTPException(status_code=503, detail="ML model not ready")

    # idempotency
    exists = db.execute(
        text("SELECT 1 FROM ml_prediction_request WHERE id = :id"),
        {"id": payload.request_id},
    ).first()

    if exists:
        raise HTTPException(status_code=409, detail="Request already processed")

    # store request
    db.execute(
        text("""
        INSERT INTO ml_prediction_request (id, source, payload)
        VALUES (:id, '1C', CAST(:payload AS JSONB))
        """),
        {
            "id": str(payload.request_id),    # ← убедитесь, что UUID → str
            "payload": json.dumps(payload.data)  # ← dict → JSON-строка
        },
    )

    # predict
    prediction, shap = svc.predict_raw(payload.data)

    # store result
    db.execute(
        text("""
        INSERT INTO ml_prediction_result
        (request_id, model_id, model_version, prediction_value, shap_values)
        VALUES (:rid, :mid, :ver, :pred, CAST(:shap AS JSONB))
        """),
        {
            "rid": str(payload.request_id),
            "mid": ML_RUNTIME_STATE["model_id"],
            "ver": ML_RUNTIME_STATE["version"],
            "pred": prediction,
            "shap": json.dumps(shap),
        },

    )

    db.commit()

    return OneCPredictResponse(
        request_id=payload.request_id,
        prediction=prediction,
        model_id=ML_RUNTIME_STATE["model_id"],
        version=ML_RUNTIME_STATE["version"],
    )
