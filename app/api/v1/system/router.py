# app/api/v1/system/router.py
"""
System API — системные технические эндпоинты.
Router  →  Service  →  Repository
         ↑
    Depends()
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.services.system_service import SystemService

from app.core.settings import settings


service = SystemService()

router = APIRouter(tags=["system"])

# ✅ КАНОНИЧЕСКИЙ HEALTH (для docker / k8s / nginx)
@router.get("/health", summary="Основной healthcheck сервиса")
def health():
    return {
        "status": "ok",
        "service": "promo-ml",
        "environment": settings.ENV,
        "version": settings.VERSION,
    }


# 🔍 Проверка сервера (legacy / optional)
@router.get("/health/server", summary="Проверка состояния сервера")
def health_server():
    """
    Возвращает технический статус сервиса.

    Returns:
        dict: Статус, время и параметры живости.
    """
    return service.health_check()


# 🔍 Проверка БД (НЕ для docker healthcheck)
@router.get("/health/db", summary="Проверка состояния postgres")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}

#  service это system_service.py

