# 📌 Товары (SKU)
from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.mixins.id import IDMixin
from models.mixins.audit import AuditMixin
from models.mixins.soft_delete import SoftDeleteMixin

from app.db.base import Base

if TYPE_CHECKING:
    from models.promo_positions import PromoPosition


class Product(IDMixin, AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "product"

    #id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))

    promo_positions: Mapped[list["PromoPosition"]] = relationship(
        back_populates="product"
    )