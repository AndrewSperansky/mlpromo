# app/schemas/dataset_schema.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class DatasetRecord(BaseModel):
    """Схема одной записи датасета для загрузки"""

    # Идентификаторы
    promo_id: str = Field(..., min_length=1, description="ID промо-акции")
    sku: str = Field(..., min_length=1, description="SKU товара")
    store_id: str = Field(..., min_length=1, description="ID магазина")

    # Категориальные
    category: str = Field(..., min_length=1, description="Категория")
    region: str = Field(..., min_length=1, description="Регион")
    store_location_type: str = Field(..., min_length=1, description="Тип локации")
    format_assortment: str = Field(..., min_length=1, description="Формат ассортимента")

    # Временные параметры
    month: int = Field(..., ge=1, le=12, description="Номер месяца (1-12)")
    week: int = Field(..., ge=1, le=52, description="Номер недели в месяце (1-52)")

    # Цены
    regular_price: float = Field(..., gt=0, description="Обычная цена")
    promo_price: float = Field(..., gt=0, description="Промо-цена")

    # Маркетинг
    promo_mechanics: Optional[str] = Field(None, description="Механика промо")
    adv_carrier: Optional[str] = Field(None, description="Рекламный носитель")
    adv_material: Optional[str] = Field(None, description="Рекламный материал")
    marketing_type: Optional[str] = Field(None, description="Тип маркетинга")

    # Справочные поля
    analog_sku: Optional[List[str]] = Field(None, description="Список SKU аналогов")

    # Целевая переменная
    k_uplift: float = Field(..., gt=0, description="Коэффициент прироста продаж")

    # Дополнительные данные
    extra_features: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные")

    class Config:
        json_schema_extra = {
            "example": {
                "promo_id": "промо-9-2025",
                "sku": "РН012912",
                "store_id": "МГЗ №287",
                "category": "Сухой",
                "region": "МСК",
                "store_location_type": "ТЦ",
                "format_assortment": "na",
                "month": 5,
                "week": 19,
                "regular_price": 999.99,
                "promo_price": 799.99,
                "promo_mechanics": "na",
                "adv_carrier": "ЖЦ",
                "adv_material": "na",
                "marketing_type": "Скидка по карте!",
                "analog_sku": [],
                "k_uplift": 13.898727394507702612,
                "extra_features": {}
            }
        }