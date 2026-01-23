# app/schemas/promo_schema.py
from datetime import datetime
from pydantic import BaseModel, Field


class PromoBase(BaseModel):
    promo_code: str = Field(..., max_length=50)
    start_date: datetime
    end_date: datetime
    is_active: bool = True


class PromoCreate(PromoBase):
    pass


class PromoUpdate(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool | None = None


class PromoRead(PromoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
