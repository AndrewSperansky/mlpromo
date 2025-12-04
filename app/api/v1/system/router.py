"""
System API — системные технические эндпоинты.
"""

from fastapi import APIRouter
from app.services.system_service import SystemService

router = APIRouter(tags=["system"])
service = SystemService()


@router.get("/health", summary="Проверка состояния сервера")
def health_check():
    """
    Возвращает технический статус сервиса.

    Returns:
        dict: Статус, время и параметры живости.
    """
    return service.health_check()
