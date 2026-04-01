# models/industrial_dataset.py

from sqlalchemy import Column, BigInteger, Text, Integer, Numeric, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base import Base


class IndustrialDatasetRaw(Base):
    __tablename__ = "industrial_dataset_raw"

    id = Column(BigInteger, primary_key=True, index=True)
    batch_id = Column(PG_UUID, nullable=True)  # ← добавляем

    # ===== ИДЕНТИФИКАТОРЫ =====
    promo_id = Column(Text)
    sku = Column(Text)
    store_id = Column(Text)

    # ===== КАТЕГОРИАЛЬНЫЕ =====
    category = Column(Text)
    region = Column(Text)
    store_location_type = Column(Text)
    format_assortment = Column(Text)

    # ===== ВРЕМЕННЫЕ =====
    month = Column(Integer)
    week = Column(Integer)

    # ===== ЦЕНОВЫЕ =====
    regular_price = Column(Numeric)
    promo_price = Column(Numeric)

    # ===== МАРКЕТИНГ =====
    promo_mechanics = Column(Text)
    adv_carrier = Column(Text)
    adv_material = Column(Text)
    marketing_type = Column(Text)


    # ===== СПРАВОЧНЫЕ =====
    analog_sku = Column(JSONB, default=list)

    # ===== ЦЕЛЕВАЯ ПЕРЕМЕННАЯ =====
    k_uplift = Column(Numeric)

    # ===== ДОПОЛНИТЕЛЬНЫЕ ДАННЫЕ =====
    extra_features = Column(JSONB, default={})

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())