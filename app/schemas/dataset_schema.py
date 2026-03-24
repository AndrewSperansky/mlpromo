# app/schemas/dataset_schema.py

from pydantic import BaseModel, Field
from typing import Optional, Any, Union
from datetime import datetime


class DatasetRecord(BaseModel):
    """Flat dataset record matching CSV structure"""

    # Обязательные поля — без default
    SKU: str = Field(..., description="SKU code")
    Store_Location_Type: str = Field(..., description="Store location type")
    StoreID: str = Field(..., description="Store identifier")
    RegularPrice: float = Field(..., description="Regular price")
    PromoPrice: float = Field(..., description="Promo price")
    PercentPriceDrop: float = Field(..., description="Percent price drop")
    VolumeRegular: float = Field(..., description="Regular weekly volume")
    HistoricalSalesPromo: float = Field(..., description="Historical promo sales")
    SalesQty_PrevModel: float = Field(..., description="Previous model sales")

    # Опциональные поля — с default
    PromoID: Optional[str] = Field(default="", description="Promo ID")
    Category: Optional[str] = Field(default="", description="Category")
    Supplier: Optional[str] = Field(default="", description="Supplier")
    Region: Optional[str] = Field(default="", description="Region")
    Date: Optional[str] = Field(default="", description="Date")
    PurchasePriceBefore: Optional[float] = Field(default=0.0, description="Purchase price before promo")
    PurchasePricePromo: Optional[float] = Field(default=0.0, description="Purchase price during promo")
    SalesQty_Promo: Optional[float] = Field(default=0.0, description="Sales quantity during promo")
    FM_Regular: Optional[float] = Field(default=0.0, description="FM regular")
    FM_Promo: Optional[float] = Field(default=0.0, description="FM promo")
    TurnoverBefore: Optional[float] = Field(default=0.0, description="Turnover before promo")
    TurnoverPromo: Optional[float] = Field(default=0.0, description="Turnover during promo")
    SeasonCoef_Week: Optional[float] = Field(default=0.0, description="Season coefficient")
    ManualCoefficientFlag: Optional[int] = Field(default=0, description="Manual coefficient flag")
    IsNewSKU: Optional[int] = Field(default=0, description="Is new SKU")
    IsAnalogSKU: Optional[int] = Field(default=0, description="Is analog SKU")
    SKU_Level2: Optional[str] = Field(default="", description="SKU level 2")
    SKU_Level3: Optional[str] = Field(default="", description="SKU level 3")
    SKU_Level4: Optional[str] = Field(default="", description="SKU level 4")
    SKU_Level5: Optional[str] = Field(default="", description="SKU level 5")

    class Config:
        json_schema_extra = {
            "example": {
                "SKU": "РН229840",
                "Store_Location_Type": "Трассовый",
                "Date": "12.01.2026 00:00:00",
                "StoreID": "МГЗ №247",
                "RegularPrice": 259.99,
                "PromoPrice": 229.99,
                "PercentPriceDrop": 11.54,
                "VolumeRegular": 119.86,
                "HistoricalSalesPromo": 442,
                "SalesQty_PrevModel": 0.25
            }
        }


class StreamMessage(BaseModel):
    """Stream message for dataset upload"""
    operation: str = Field(..., description="batch_start, record, batch_end, heartbeat, complete, error")
    batch_id: Optional[str] = None
    sequence: Optional[int] = None
    total_count: Optional[int] = None
    data: Optional[Any] = None  # ← Changed: accepts any JSON-serializable data
    error: Optional[str] = None
    timestamp: Optional[str] = None