# app/api/v1/ml/prediction_schema.py

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, Dict, Any, List
from uuid import UUID


class PredictionRequest(BaseModel):
    prediction_date: date = Field(..., description="Дата прогноза")
    features: Dict[str, float]
    promo_code: str = Field(..., description="Код промо")
    sku: str = Field(..., description="SKU товара")


class ShapValue(BaseModel):
    feature: str
    effect: float


class PredictionResponse(BaseModel):
    promo_code: str
    sku: str
    date: date

    prediction: Optional[float] = None
    baseline: Optional[float] = None
    uplift: Optional[float] = None

    # ✅ исправлено: feature как str, effect как float
    shap_values: List[ShapValue] = Field(default_factory=list)

    ml_model_id: str
    version: str
    trained_at: Optional[datetime] = None

    features: Optional[Dict[str, Any]] = None
    fallback_used: bool
    reason: Optional[str] = None


class OneCPredictRequest(BaseModel):
    request_id: UUID
    data: Dict[str, Any]


class OneCPredictResponse(BaseModel):
    request_id: UUID
    prediction: float
    ml_model_id: str
    version: str