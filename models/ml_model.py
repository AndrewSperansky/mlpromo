# models/ml_model.py
# ML-модели (реестр моделей)

from sqlalchemy import String, Boolean, JSON, Text, DateTime, func, Integer
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base
from models.mixins.id import IDMixin
from models.mixins.audit import AuditMixin


from pathlib import Path
from catboost import CatBoostRegressor


class MLModel(IDMixin, AuditMixin, Base):
    __tablename__ = "ml_model"

    id = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(100))
    algorithm: Mapped[str] = mapped_column(String(50))  # catboost, xgboost, etc
    dataset_version_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=True,)

    version: Mapped[str] = mapped_column(String(20))

    model_type: Mapped[str] = mapped_column(String)
    target: Mapped[str] = mapped_column(String)

    features: Mapped[list[str]] = mapped_column(JSON)
    metrics: Mapped[dict | None] = mapped_column(JSON)

    model_path: Mapped[str] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    trained_rows_count: Mapped[int] = mapped_column(nullable=False, default=0)


class MLModelManager:
    def __init__(self, model_path: Path):
        self.model_path = model_path
        self.model: CatBoostRegressor | None = None

    def load(self) -> bool:
        if not self.model_path.exists():
            return False

        model = CatBoostRegressor()
        model.load_model(str(self.model_path))

        # 🔥 ВАЖНО: сохраняем модель
        self.model = model
        return True

    def is_loaded(self) -> bool:
        return self.model is not None



