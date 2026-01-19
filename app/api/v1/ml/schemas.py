# app/api/v1/ml/schemas.py

from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Optional


class PredictionRequest(BaseModel):
    prediction_date: date = Field(..., description="Дата прогноза")  # Изменено, что делать?
    price: float = Field(..., gt=0)
    discount: float = Field(..., ge=0)
    avg_sales_7d: float = Field(..., ge=0)
    promo_days_left: int = Field(..., ge=0)
    promo_code: str = Field(..., description="Код промо")
    sku: str = Field(..., description="SKU товара")




class PredictionResponse(BaseModel):
    promo_code: str
    sku: str
    date: date

    prediction: float

    model_id: str           # Изменено, что делать?
    version: str            # Изменено, что делать?
    trained_at: Optional[datetime] = None   # ✅ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ

    features: dict
    fallback_used: bool
