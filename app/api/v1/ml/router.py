from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.ml.model_loader import ModelLoader
from app.services.ml_training_service import MLTrainingService
from app.services.ml_prediction_service import MLPredictionService

router = APIRouter(tags=["ml"])


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
