# app/api/v1/ml/schemas.py
from datetime import date
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    date: date = Field(..., description="Дата прогноза")
    price: float = Field(..., gt=0)
    discount: float = Field(..., ge=0)
    avg_sales_7d: float = Field(..., ge=0)
    promo_days_left: int = Field(..., ge=0)
    promo_code: str = Field(..., json_schema_extra={"example": "PROMO_DAIRY_JAN"})
    sku: str = Field(..., json_schema_extra={"example": "MILK_1L"})




class PredictionResponse(BaseModel):
    promo_code: str
    sku: str
    date: date

    predicted_sales_qty: float

    model_name: str
    model_version: str
    trained_at: str

    fallback_used: bool
