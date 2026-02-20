# app/services/system_service.py

"""
System Service: технические методы системы.
"""

from datetime import datetime, timezone
import logging
from app.core.settings import settings
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.ml.telemetry import TelemetryExporter

logger = logging.getLogger("promo_ml")


class SystemService:
    """
    Сервис системных операций: health-check, метаинформация и пр.
    """


    def health_check(self) -> dict:
        """
        Возвращает состояние системы.

        Returns:
            dict: Статус сервиса и текущее время.
        """
        logger.info("Healthcheck executed")

        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "promo-ml",
        }


    def health_db(self, db: Session) -> dict:

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


    def get_metrics(self) -> dict:
        """
        Stage 5 — Telemetry snapshot provider.
        """

        exporter = TelemetryExporter()

        return exporter.collect()


    # =============================
    # Runtime Admin Operations
    # =============================

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
        ML_RUNTIME_STATE["last_retrain_request"] = datetime.now(timezone.utc).isoformat()

        return {
            "retrain_requested": True,
            "timestamp": ML_RUNTIME_STATE["last_retrain_request"],
        }

    def get_runtime_state(self) -> dict:
        from app.ml.runtime_state import ML_RUNTIME_STATE

        return ML_RUNTIME_STATE

    # =============================
    # Aggregated Overview
    # =============================

    def get_overview(self) -> dict:
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
            },
            "telemetry": telemetry,
            "errors": ML_RUNTIME_STATE.get("errors", []),
            "warnings": ML_RUNTIME_STATE.get("warnings", []),
        }