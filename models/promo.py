# 📌 Справочники: Промо-акции
from sqlalchemy import String, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class Promo(Base):
    __tablename__ = "promo"

    id: Mapped[int] = mapped_column(primary_key=True)
    promo_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    start_date: Mapped[Date]
    end_date: Mapped[Date]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
