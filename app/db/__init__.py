from app.db.base import Base


# Импортируем все модели для регистрации в metadata
from models import Promo, PromoPosition, Product, MLModel

__all__ = [
    "Base",
    "Promo",
    "PromoPosition",
    "Product",
    "MLModel",
]