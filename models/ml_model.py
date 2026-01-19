# models/ml_model.py
# ML-модели (реестр моделей)

from sqlalchemy import String, Boolean, JSON, Text, DateTime, func, Integer
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from models.mixins.id import IDMixin
from models.mixins.audit import AuditMixin

class MLModel(IDMixin, AuditMixin, Base):
    __tablename__ = "ml_model"

    id = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(100), unique=True)
    algorithm: Mapped[str] = mapped_column(String(50))  # catboost, xgboost, etc

    version: Mapped[str] = mapped_column(String(20))

    model_type: Mapped[str] = mapped_column(String)
    target: Mapped[str] = mapped_column(String)

    features: Mapped[list[str]] = mapped_column(JSON)
    metrics: Mapped[dict | None] = mapped_column(JSON)

    model_path: Mapped[str] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )






