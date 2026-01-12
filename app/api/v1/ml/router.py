from fastapi import APIRouter, Depends
from pydantic import BaseModel

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.ml.model_loader import ModelLoader
from app.services.ml_training_service import MLTrainingService
from app.services.ml_prediction_service import MLPredictionService
from app.api.v1.ml.predict import router as predict_router

router = APIRouter(prefix="/ml", tags=["ml"])
router.include_router(predict_router)

# POST /api/v1/ml/predict

# ========== DEPENDENCIES ==========


def get_prediction_service():
    """
    Возвращает сервис предсказаний с загруженной ML моделью.
    """
    model = ModelLoader.load()
    return MLPredictionService(model)


def get_training_service():
    return MLTrainingService()


# ========== REQUEST MODELS ==========


class TrainRequest(BaseModel):
    dataset_path: str
    config: dict | None = {}


class PredictionRequest(BaseModel):
    features: dict


# ========== ENDPOINTS ==========


@router.post("/train", summary="Обучение ML модели")
def train_model(
    payload: TrainRequest, svc: MLTrainingService = Depends(get_training_service)
):
    """
    Запускает обучение модели CatBoost.
    """
    result = svc.train(
        dataset_path=payload.dataset_path,
        config=payload.config,
    )
    return result


@router.post("/predict", summary="Предсказание ML модели")
def predict(
    payload: PredictionRequest,
    svc: MLPredictionService = Depends(get_prediction_service),
):
    """
    Выполняет предсказание ML модели + SHAP объяснения.
    """
    return svc.predict(payload.features)


# Read-only ML-dataset API

@router.get("/dataset", summary="ML dataset (read-only)")
def get_ml_dataset(
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
):
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

    result = db.execute(
        query,
        {"limit": limit, "offset": offset},
    )

    rows = result.mappings().all()
    return {
        "count": len(rows),
        "items": rows,
    }