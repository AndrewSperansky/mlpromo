# 📌 Справочники: Промо-акции
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from models.mixins.id import IDMixin
from models.mixins.audit import AuditMixin
from models.mixins.soft_delete import SoftDeleteMixin
from datetime import datetime
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from models.promo_positions import PromoPosition

class Promo(IDMixin, AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "promo"

    promo_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    positions: Mapped[list["PromoPosition"]] = relationship(
        back_populates="promo",
        cascade="all, delete-orphan",
    )


