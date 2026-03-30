# models/industrial_dataset.py

from sqlalchemy import Column, BigInteger, Text, Integer, Numeric, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class IndustrialDatasetRaw(Base):
    __tablename__ = "industrial_dataset_raw"

    id = Column(BigInteger, primary_key=True, index=True)

    # Инференс-поля
    promo_id = Column(Text)
    sku = Column(Text)
    store_id = Column(Text)
    promo_week1 = Column(Integer)
    promo_week2 = Column(Integer)
    regular_price = Column(Numeric)
    promo_price = Column(Numeric)
    prev_promo_id = Column(Text)
    adv_carrier = Column(Text)
    adv_material = Column(Text)
    promo_mechanics = Column(Text)

    # Категориальные поля
    store_location_type = Column(Text)
    region = Column(Text)
    format_assortment = Column(Text)
    sku_level_2 = Column(Text)
    sku_level_3 = Column(Text)
    sku_level_4 = Column(Text)
    sku_level_5 = Column(Text)
    category = Column(Text)
    is_new_sku = Column(Integer)
    analog_sku = Column(Text)

    # Целевые переменные
    promo_week1_sales_qty = Column(Numeric)
    promo_week2_sales_qty = Column(Numeric)

    # Исторические данные (52 недели) — можно сгенерировать динамически
    # Либо оставить как есть

    # JSONB
    extra_features = Column(JSON, default={})

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())