# app/api/v1/ml/schemas.py

from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID


class PredictionRequest(BaseModel):
    prediction_date: date = Field(..., description="Дата прогноза")
    price: float = Field(..., gt=0)
    discount: float = Field(..., ge=0)
    avg_sales_7d: float = Field(..., ge=0)
    promo_days_left: int = Field(..., ge=0)
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

    ml_model_id: str
    version: str
    trained_at: Optional[datetime] = None

    features: Optional[Dict[str, Any]] = None
    shap: List[ShapValue] = Field(default_factory=list)

    fallback_used: bool
    reason: Optional[str] = None


class OneCPredictRequest(BaseModel):
    request_id: UUID
    data: Dict[str, Any]


class OneCPredictResponse(BaseModel):
    request_id: UUID
    prediction: float
    model_id: str
    version: str