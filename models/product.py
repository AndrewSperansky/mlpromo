# 📌 Товары (SKU)
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
