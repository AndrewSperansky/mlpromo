# app/api/v1/ml/prediction_schema.py

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, Dict, Any, List
# from uuid import UUID


class PredictionRequest(BaseModel):
    prediction_date: date = Field(
        ...,
        description="Дата прогноза"
    )

    features: Dict[str, float] = Field(
        ...,
        description="Словарь признаков модели. Должен содержать все 16 признаков."
    )

    promo_code: str = Field(
        ...,
        description="Код промо-акции"
    )

    sku: str = Field(
        ...,
        description="SKU товара"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prediction_date": "2026-03-24",
                "promo_code": "PROMO10",
                "sku": "РН229840",
                "features": {
                    "RegularPrice": 259.99,
                    "PromoPrice": 229.99,
                    "PurchasePriceBefore": 116.71,
                    "PurchasePricePromo": 116.71,
                    "PercentPriceDrop": 11.54,
                    "VolumeRegular": 119.86,
                    "HistoricalSalesPromo": 442.0,
                    "SalesQty_PrevModel": 0.25,
                    "FM_Regular": 50.62,
                    "FM_Promo": 44.18,
                    "TurnoverBefore": 31162.4,
                    "TurnoverPromo": 28898.24,
                    "SeasonCoef_Week": 1.0,
                    "ManualCoefficientFlag": 0.0,
                    "IsNewSKU": 0.0,
                    "IsAnalogSKU": 0.0
                }
            }
        }



class ShapValue(BaseModel):
    feature: str
    effect: float


class FinanceMetrics(BaseModel):
    """Финансовые метрики для промо"""
    SKU: str
    NewSales: float


class PredictionResponse(BaseModel):
    promo_code: str
    sku: str
    date: date

    prediction: Optional[float] = None
    baseline: Optional[float] = None
    uplift: Optional[float] = None

    # feature как str, effect как float
    shap_values: List[ShapValue] = Field(default_factory=list)

    ml_model_id: str
    version: str
    trained_at: Optional[datetime] = None

    features: Optional[Dict[str, Any]] = None
    fallback_used: bool
    reason: Optional[str] = None

    finance_metrics: Optional[FinanceMetrics] = Field(default=None, description="Финансовые метрики")
