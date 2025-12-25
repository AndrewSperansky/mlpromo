# Результаты предсказаний (обязательно)

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from models.mixins.id import IDMixin
from models.mixins.audit import AuditMixin

if TYPE_CHECKING:
    from models.ml_model import MLModel


class Prediction(IDMixin, AuditMixin, Base):
    __tablename__ = "prediction"

    id: Mapped[int] = mapped_column(primary_key=True)

    ml_model_id: Mapped[int] = mapped_column(
        ForeignKey("ml_model.id"),
        index=True,
        nullable=False,
    )

    predicted_sales: Mapped[float] = mapped_column(Float, nullable=False)



    model: Mapped["MLModel"] = relationship("MLModel")

