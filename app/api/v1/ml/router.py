from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ml_training_service import MLTrainingService
from app.services.ml_prediction_service import MLPredictionService


router = APIRouter(tags=["ml"])
train_service = MLTrainingService()
service = MLPredictionService()


class TrainRequest(BaseModel):
    dataset_path: str
    config: dict


@router.post("/train", summary="Обучение ML модели")
def train_model(payload: TrainRequest):
    """
    Запускает обучение ML модели CatBoost.

    Args:
        payload (TrainRequest): Путь к датасету и параметры модели.

    Returns:
        dict: Путь к сохранённой модели.
    """
    model_path = train_service.train(
        dataset={"X_train": None, "y_train": None},  # позже пришьём loader
        config=payload.config,
    )
    return {"model_saved_to": model_path}


class PredictionRequest(BaseModel):
    # В дальнейшем заменим на конкретные поля датасета
    features: dict


@router.post("/predict", summary="Предсказание ML модели")
def predict(payload: PredictionRequest):
    """
    Выполняет предсказание ML-модели на основе входных параметров.

    Args:
        payload (PredictionRequest): Входные признаки модели.

    Returns:
        dict: Предсказание + версия модели.
    """
    return service.predict(payload.features)


""" @router.post("/predict", response_model=Dict)
async def predict(payload: Dict, model=Depends(get_model)):
    # здесь вызвать ваш сервис-предсказания; пример:
    from app.services.predictor import predict_with_shap

    return predict_with_shap(payload, model) """
