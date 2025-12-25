from typing import TYPE_CHECKING
from datetime import date
from sqlalchemy import ForeignKey, Date, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.promo import Promo
    from models.product import Product


class PromoPosition(Base):
    __tablename__ = "promo_position"

    id: Mapped[int] = mapped_column(primary_key=True)

    promo_id: Mapped[int] = mapped_column(
        ForeignKey("promo.id"),
        index=True,
        nullable=False,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id"),
        index=True,
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Дата действия промо",
    )

    price: Mapped[float] = mapped_column(Float, nullable=False)
    discount: Mapped[float] = mapped_column(Float, nullable=False)
    sales_qty: Mapped[int] = mapped_column(Integer, nullable=False)

    promo: Mapped["Promo"] = relationship("Promo")
    product: Mapped["Product"] = relationship("Product")
