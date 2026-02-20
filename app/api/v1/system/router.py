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


from app.ml.runtime_state import ML_RUNTIME_STATE

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
        "version": settings.API_CONTRACT_VERSION,
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


@router.get("/status")
def system_status():
    """
    Basic runtime status endpoint.
    """

    return {
        "status": ML_RUNTIME_STATE.get("status"),
        "model_loaded": ML_RUNTIME_STATE.get("model_loaded"),
        "active_model_version": ML_RUNTIME_STATE.get("version"),
        "errors": ML_RUNTIME_STATE.get("errors"),
        "warnings": ML_RUNTIME_STATE.get("warnings"),
    }


@router.get("/metrics")
def system_metrics():
    """
    Stage 5 — Telemetry endpoint.

    Returns runtime ML telemetry snapshot.
    """

    return service.get_metrics()


# =============================
# Runtime Admin
# =============================

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


# =============================
# Aggregated Overview
# =============================

@router.get("/overview")
def overview():
    return service.get_overview()