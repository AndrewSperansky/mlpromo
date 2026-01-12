# app/api/v1/ml/predict.py
#from datetime import date
#import joblib
#from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session
from app.db.session import get_db

from app.api.v1.ml.schemas import (
    PredictionRequest,
    PredictionResponse,
)
from app.ml.dataset.ml_dataset import fetch_features
from app.ml.registry import load_active_model

router = APIRouter(prefix="/ml", tags=["ML"])


@router.post("/predict", response_model=PredictionResponse)
def predict(
    request: PredictionRequest,
    db: Session = Depends(get_db),
):
    try:
        features, fallback_used = fetch_features(
            db=db,
            promo_code=request.promo_code,
            sku=request.sku,
            target_date=request.date,
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    model, model_row = load_active_model(db)

    prediction = float(model.predict(features)[0])

    return PredictionResponse(
        promo_code=request.promo_code,
        sku=request.sku,
        date=request.date,
        predicted_sales_qty=prediction,
        model_name=model_row.name,
        model_version=model_row.version,
        trained_at=model_row.trained_at.isoformat(),
        fallback_used=fallback_used,
    )

