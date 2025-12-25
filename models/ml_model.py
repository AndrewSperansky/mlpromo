# ML-модели (реестр моделей)
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from models.mixins.id import IDMixin
from models.mixins.audit import AuditMixin

class MLModel(IDMixin, AuditMixin, Base):
    __tablename__ = "ml_model"


    name: Mapped[str] = mapped_column(String(100), unique=True)
    algorithm: Mapped[str] = mapped_column(String(50))  # catboost, xgboost, etc
    version: Mapped[str] = mapped_column(String(20))






