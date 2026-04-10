# app/db/__init__.py

from app.db.base import Base

# Импортируем все модели для регистрации в metadata

__all__ = [
    "Base",
]