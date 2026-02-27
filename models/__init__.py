# models/__init__.py
# Этот файл гарантирует, что все модели импортированы в правильном порядке
from models.promo_position import PromoPosition  # сначала дочерние
from models.promo import Promo  # потом родительские
from models.product import Product
from models.ml_model import MLModel

__all__ = [
    "Promo",
    "PromoPosition",
    "Product",
    "MLModel",
]
