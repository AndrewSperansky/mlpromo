# app/schemas/prediction_schema.py

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, Dict, Any, List


class PredictionRequest(BaseModel):
    """Запрос на предсказание — возвращает коэффициент прироста"""

    # 🔥 Промо-акция
    promo_id: str = Field(..., min_length=1, description="ID промо-акции")

    # Временные параметры
    week: int = Field(..., ge=1, le=52, description="Номер недели в году (1-52)")
    month: int = Field(..., ge=1, le=12, description="Номер месяца в году (1-12)")

    # Товар и категория
    sku: str = Field(..., min_length=1, description="SKU товара")
    category: str = Field(..., min_length=1, description="Категория")

    # Цены
    regular_price: float = Field(..., gt=0, description="Обычная цена")
    promo_price: float = Field(..., gt=0, description="Промо-цена")

    # Магазин и локация
    store_id: str = Field(..., min_length=1, description="ID магазина")
    region: str = Field(..., min_length=1, description="Регион")
    store_location_type: str = Field(..., min_length=1, description="Тип локации")
    format_assortment: str = Field(..., min_length=1, description="Формат ассортимента")

    # Маркетинг и механики
    adv_carrier: Optional[str] = Field(None, description="Рекламный носитель")
    adv_material: Optional[str] = Field(None, description="Рекламный материал")
    promo_mechanics: Optional[str] = Field(None, description="Механика промо")
    marketing_type: Optional[str] = Field(None, description="Тип маркетинга")


    # Справочные поля
    analog_sku: Optional[List[str]] = Field(None, description="Список SKU аналогов")

    # Дополнительные данные
    extra_features: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные")

    # Для обратной совместимости
    promo_code: Optional[str] = Field(None, description="Код промо-акции (устарело)")
    prediction_date: Optional[date] = Field(None, description="Дата прогноза (устарело)")


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
    """Ответ API — возвращает коэффициент прироста"""

    # Входные параметры (для контекста)
    promo_id: str
    sku: str
    store_id: str
    category: str
    region: str
    store_location_type: str
    format_assortment: str
    week: int
    month: int
    regular_price: float
    promo_price: float
    marketing_type: Optional[str] = None

    # 🔥 ОСНОВНОЙ РЕЗУЛЬТАТ
    k_uplift: Optional[float] = Field(None, description="Коэффициент прироста (прогноз)")
    confidence: Optional[float] = Field(None, description="Уверенность прогноза (0-1)")

    # SHAP объяснения
    shap_values: List[ShapValue] = Field(default_factory=list)

    # Метаданные модели
    ml_model_id: str
    version: str
    trained_at: Optional[datetime] = None

    # Дополнительная информация
    features_used: Optional[Dict[str, Any]] = None
    fallback_used: bool = False
    reason: Optional[str] = None

    # Исторический контекст
    historical_context: Optional[HistoricalContext] = None

    # Для обратной совместимости
    promo_code: Optional[str] = None
    date: Optional[date] = None
    prediction: Optional[float] = None
    baseline: Optional[float] = None
    uplift: Optional[float] = None