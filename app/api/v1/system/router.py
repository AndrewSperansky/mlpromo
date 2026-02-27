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


# ==========================================================
# HEALTH
# ==========================================================

@router.get("/health", summary="Основной healthcheck сервиса")
def health():
    """
    Канонический healthcheck для docker / k8s / nginx.
    НЕ зависит от ML runtime.
    """
    return {
        "status": "ok",
        "service": "promo-ml",
        "environment": settings.ENV,
        "version": settings.API_CONTRACT_VERSION,
    }


@router.get("/health/server", summary="Проверка состояния сервера")
def health_server():
    """
    Возвращает технический статус сервиса.
    """
    return service.health_check()


@router.get("/health/db", summary="Проверка состояния postgres")
def health_db(db: Session = Depends(get_db)):
    """
    Проверка соединения с БД.
    НЕ использовать как docker healthcheck.
    """
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


# ==========================================================
# SYSTEM STATUS
# ==========================================================

@router.get("/status")
def system_status():
    """
    Basic runtime status endpoint.
    Делегирует в SystemService.
    """
    return service.get_status()


@router.get("/metrics")
def system_metrics():
    """
    Stage 5 — Telemetry endpoint.
    Returns runtime ML telemetry snapshot.
    """
    return service.get_metrics()


# ==========================================================
# RUNTIME ADMIN
# ==========================================================

@router.post("/freeze")
def freeze():
    return service.freeze()


@router.post("/unfreeze")
def unfreeze():
    return service.unfreeze()


@router.post("/clear-drift")
def clear_drift():
    return service.clear_drift()


@router.post("/force-retrain")
def force_retrain():
    return service.force_retrain()


@router.get("/runtime-state")
def runtime_state():
    return service.get_runtime_state()


# ==========================================================
# AGGREGATED OVERVIEW
# ==========================================================

@router.get("/overview")
def overview():
    """
    Stage 5.4 — Aggregated System Overview.
    Объединяет:
        - status
        - metrics
        - runtime state
        - registry state (если реализовано в service)
    """
    return service.get_overview()