# app/schemas/prediction_schema.py

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, Dict, Any, List


class PredictionRequest(BaseModel):
    """Запрос на предсказание (инференс)"""

    promo_code: str = Field(..., description="Код промо-акции")
    sku: str = Field(..., description="SKU товара")
    store_id: str = Field(..., description="ID магазина")
    prediction_date: date = Field(..., description="Дата прогноза")

    promo_week1: int = Field(..., description="Номер первой недели промо", ge=1, le=52)
    promo_week2: int = Field(..., description="Номер второй недели промо", ge=1, le=52)

    regular_price: float = Field(..., description="Обычная цена", gt=0)
    promo_price: float = Field(..., description="Промо-цена", gt=0)

    prev_promo_id: Optional[str] = Field(None, description="ID предыдущей промо-акции")
    adv_carrier: Optional[str] = Field(None, description="Рекламный носитель")
    adv_material: Optional[str] = Field(None, description="Рекламный материал")
    promo_mechanics: Optional[str] = Field(None, description="Механика промо")

    class Config:
        json_schema_extra = {
            "example": {
                "promo_code": "Промо-1-2026",
                "sku": "РН229840",
                "store_id": "МГЗ №366",
                "prediction_date": "2026-03-27",
                "promo_week1": 10,
                "promo_week2": 11,
                "regular_price": 259.99,
                "promo_price": 229.99,
                "prev_promo_id": "Промо-4-2025",
                "adv_carrier": "Паук",
                "adv_material": "Каталог",
                "promo_mechanics": "1+1"
            }
        }


class ShapValue(BaseModel):
    feature: str
    effect: float


class FinanceMetrics(BaseModel):
    """Финансовые метрики для промо"""
    SKU: str
    NewSales: float


class PromoEffectiveness(BaseModel):
    """Метрики эффективности промоакции"""
    promo_id: str
    total_records: int
    total_sales: float
    total_baseline: float
    avg_uplift: float
    avg_discount: float
    effectiveness: str
    message: str


class HistoricalContext(BaseModel):
    """Исторические данные по SKU"""
    sku: str
    store_id: Optional[str] = None
    total_records: int
    avg_sales: float
    avg_regular_sales: float
    avg_turnover: float
    sales_volatility: float
    max_sales: float
    min_sales: float
    last_promo: Optional[Dict[str, Any]] = None
    seasonal_patterns: Optional[Dict[str, float]] = None


class PredictionResponse(BaseModel):
    promo_code: str
    sku: str
    store_id: Optional[str] = None
    date: date

    prediction: Optional[float] = None
    baseline: Optional[float] = None
    uplift: Optional[float] = None

    shap_values: List[ShapValue] = Field(default_factory=list)

    ml_model_id: str
    version: str
    trained_at: Optional[datetime] = None

    features: Optional[Dict[str, Any]] = None
    fallback_used: bool
    reason: Optional[str] = None

    finance_metrics: Optional[FinanceMetrics] = None
    promo_effectiveness: Optional[PromoEffectiveness] = None
    historical_context: Optional[HistoricalContext] = None