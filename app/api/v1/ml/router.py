# app/api/v1/ml/router.py

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.ml_training_service import MLTrainingService
from app.services.ml_prediction_service import MLPredictionService

from app.api.v1.ml.schemas import (
    PredictionRequest,
    PredictionResponse,
)


from app.ml.runtime_state import ML_RUNTIME_STATE

router = APIRouter(tags=["ml"])

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

