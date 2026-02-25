# app/services/system_service.py

"""
System Service: технические методы системы.
Router → Service → Repository
"""

from datetime import datetime, timezone
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.ml.telemetry import TelemetryExporter

logger = logging.getLogger("promo_ml")


class SystemService:
    """
    Сервис системных операций:
    - health-check
    - telemetry
    - runtime admin
    - aggregated overview
    """

    # ==========================================================
    # HEALTH
    # ==========================================================

    def health_check(self) -> dict:
        """
        Возвращает состояние сервиса.
        Используется для /health/server
        """

        logger.info("Healthcheck executed")

        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "promo-ml",
        }

    def health_db(self, db: Session) -> dict:
        """
        Проверка соединения с БД.
        НЕ для docker healthcheck.
        """

        db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "checks": {
                "database": "ok",
                "config": "ok",
            },
            "environment": settings.ENV,
            "version": settings.VERSION,
        }

    # ==========================================================
    # TELEMETRY
    # ==========================================================

    def get_metrics(self) -> dict:
        """
        Stage 5 — Telemetry snapshot provider.
        Источник для /metrics
        """

        exporter = TelemetryExporter()
        return exporter.collect()

    # ==========================================================
    # RUNTIME ADMIN OPERATIONS
    # ==========================================================

    def freeze(self) -> dict:
        from app.ml.runtime_state import ML_RUNTIME_STATE

        ML_RUNTIME_STATE["freeze_flag"] = True

        return {
            "freeze_flag": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def unfreeze(self) -> dict:
        from app.ml.runtime_state import ML_RUNTIME_STATE

        ML_RUNTIME_STATE["freeze_flag"] = False

        return {
            "freeze_flag": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def clear_drift(self) -> dict:
        from app.ml.runtime_state import ML_RUNTIME_STATE

        ML_RUNTIME_STATE["drift_flag"] = False

        return {
            "drift_flag": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def force_retrain(self) -> dict:
        from app.ml.runtime_state import ML_RUNTIME_STATE

        ML_RUNTIME_STATE["retrain_requested"] = True
        ML_RUNTIME_STATE["last_retrain_request"] = datetime.now(
            timezone.utc
        ).isoformat()

        return {
            "retrain_requested": True,
            "timestamp": ML_RUNTIME_STATE["last_retrain_request"],
        }

    def get_runtime_state(self) -> dict:
        from app.ml.runtime_state import ML_RUNTIME_STATE
        return ML_RUNTIME_STATE

    # ==========================================================
    # STATUS (делегат для router)
    # ==========================================================

    def get_status(self) -> dict:
        """
        Базовый runtime статус.
        Используется для /status
        """

        from app.ml.runtime_state import ML_RUNTIME_STATE

        return {
            "status": ML_RUNTIME_STATE.get("status"),
            "model_loaded": ML_RUNTIME_STATE.get("model_loaded"),
            "active_model_version": ML_RUNTIME_STATE.get("version"),
            "ml_model_id": ML_RUNTIME_STATE.get("ml_model_id"),
            "errors": ML_RUNTIME_STATE.get("errors", []),
            "warnings": ML_RUNTIME_STATE.get("warnings", []),
        }

    # ==========================================================
    # AGGREGATED OVERVIEW (Stage 5.4)
    # ==========================================================

    def get_overview(self) -> dict:
        """
        Aggregated System Overview.
        Используется Dashboard.
        Объединяет:
            - runtime
            - telemetry
            - errors / warnings
        """

        from app.ml.runtime_state import ML_RUNTIME_STATE

        telemetry = self.get_metrics()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "runtime": {
                "ml_model_id": ML_RUNTIME_STATE.get("ml_model_id"),
                "version": ML_RUNTIME_STATE.get("version"),
                "model_loaded": ML_RUNTIME_STATE.get("model_loaded"),
                "freeze_flag": ML_RUNTIME_STATE.get("freeze_flag"),
                "drift_flag": ML_RUNTIME_STATE.get("drift_flag"),
                "retrain_requested": ML_RUNTIME_STATE.get("retrain_requested"),
            },
            "telemetry": telemetry,
            "errors": ML_RUNTIME_STATE.get("errors", []),
            "warnings": ML_RUNTIME_STATE.get("warnings", []),
        }