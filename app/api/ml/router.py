# app/api/ml/router.py
from fastapi import APIRouter, Depends
from app.api.dependencies import get_model  # предполагаемая зависимость
from typing import Dict

router = APIRouter()


@router.post("/predict", response_model=Dict)
async def predict(payload: Dict, model=Depends(get_model)):
    # здесь вызвать ваш сервис-предсказания; пример:
    from app.api.ml.predictor import predict_with_shap

    return predict_with_shap(payload, model)
