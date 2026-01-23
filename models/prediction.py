# models/prediction.py
# Результаты предсказаний (обязательно)

from sqlalchemy import (
    Integer,
    Float,
    String,
    Date,
    Boolean,
    JSON,
    ForeignKey,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from models.mixins.id import IDMixin
from models.mixins.audit import AuditMixin


class Prediction(IDMixin, AuditMixin, Base):
    __tablename__ = "prediction"

    promo_code: Mapped[str] = mapped_column(String, nullable=False)
    sku: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False)

    predicted_sales_qty: Mapped[float] = mapped_column(Float, nullable=False)

    features: Mapped[dict] = mapped_column(JSON, nullable=False)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)

    ml_model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ml_model.id"),
        nullable=False,
    )

