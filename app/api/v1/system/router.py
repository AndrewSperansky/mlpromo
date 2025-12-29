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

router = APIRouter(tags=["system"])
service = SystemService()


@router.get("/health/server", summary="Проверка состояния сервера")
def health_server():
    """
    Возвращает технический статус сервиса.

    Returns:
        dict: Статус, время и параметры живости.
    """
    return service.health_check()


@router.get("/health/db", summary="Проверка состояния postgres")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}

#  service это system_service.py

