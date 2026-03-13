from app.db.base import Base


# Импортируем все модели для регистрации в metadata
from models import  MLModel

__all__ = [
    "Base",
    "MLModel",
]