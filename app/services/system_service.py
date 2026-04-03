# app/services/system_service.py

from datetime import datetime, timezone
import logging
from typing import Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.ml.telemetry import TelemetryExporter
from app.ml.runtime_state import ML_RUNTIME_STATE
from app.ml.self_healing.retrain_detector import RetrainDetector

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
        """

        db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "checks": {
                "database": "ok",
                "config": "ok",
            },
            "environment": settings.ENV,
            "version": settings.API_CONTRACT_VERSION,
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
        ML_RUNTIME_STATE["freeze_flag"] = True

        return {
            "freeze_flag": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def unfreeze(self) -> dict:
        ML_RUNTIME_STATE["freeze_flag"] = False

        return {
            "freeze_flag": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def clear_drift(self) -> dict:
        ML_RUNTIME_STATE["drift_flag"] = False

        return {
            "drift_flag": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def force_retrain(self) -> dict:
        """
       Проверяет необходимость retrain и создаёт рекомендацию.
       НЕ запускает обучение автоматически — human-in-the-loop!
       """
        logger.info("🔍 Checking retrain need...")

        with RetrainDetector() as detector:
            recommendation = detector.check_and_recommend()

        if recommendation["needed"]:
            ML_RUNTIME_STATE["retrain_recommended"] = True
            ML_RUNTIME_STATE["retrain_recommended_reason"] = recommendation["reason"]
            ML_RUNTIME_STATE["retrain_recommended_at"] = datetime.now(timezone.utc).isoformat()
            ML_RUNTIME_STATE["retrain_candidate_metrics"] = recommendation.get("candidate_metrics")

            logger.info(
                f"📢 Retrain recommendation created",
                extra={
                    "reason": recommendation["reason"],
                    "priority": recommendation["priority"],
                    "new_data_count": recommendation["new_data_count"],
                }
            )
        else:
            logger.info("✅ No retrain needed")

        return {
            "retrain_recommended": recommendation["needed"],
            "reason": recommendation["reason"],
            "priority": recommendation["priority"],
            "new_data_count": recommendation["new_data_count"],
            "days_since_train": recommendation["days_since_train"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_retrain_recommendation(self) -> dict:
        """Возвращает текущую рекомендацию по retrain"""
        return {
            "recommended": ML_RUNTIME_STATE.get("retrain_recommended", False),
            "reason": ML_RUNTIME_STATE.get("retrain_recommended_reason"),
            "candidate_metrics": ML_RUNTIME_STATE.get("retrain_candidate_metrics"),
            "candidate_id": ML_RUNTIME_STATE.get("retrain_candidate_id"),
            "candidate_version": ML_RUNTIME_STATE.get("retrain_candidate_version"),
            "recommended_at": ML_RUNTIME_STATE.get("retrain_recommended_at"),
        }

    def approve_retrain(self) -> dict:
        """
        Пользователь одобрил retrain — запускаем обучение и promote (activate).
        """
        if not ML_RUNTIME_STATE.get("retrain_recommended"):
            return {
                "status": "no_recommendation",
                "message": "No retrain recommendation to approve",
            }

        logger.info("👍 Retrain approved by user, starting training...")

        # Запускаем обучение с promote=true
        from app.ml.train.train_pipeline import train_pipeline

        try:
            result = train_pipeline(promote=True, trigger="human_approved")

            # Сбрасываем рекомендацию
            ML_RUNTIME_STATE["retrain_recommended"] = False
            ML_RUNTIME_STATE["retrain_recommended_reason"] = None
            ML_RUNTIME_STATE["retrain_candidate_metrics"] = None
            ML_RUNTIME_STATE["retrain_candidate_id"] = None
            ML_RUNTIME_STATE["retrain_candidate_version"] = None
            ML_RUNTIME_STATE["retrain_recommended_at"] = None

            return {
                "status": "retrain_started",
                "message": "Training started with promotion",
                "train_result": {
                    "model_id": result.get("model_id"),
                    "metrics": result.get("metrics"),
                    "promoted": result.get("promoted", True),
                },
            }

        except Exception as e:
            logger.error(f"Retrain failed: {e}")
            return {
                "status": "failed",
                "message": f"Training failed: {str(e)}",
            }

    def dismiss_retrain(self) -> dict:
        """
        Пользователь отклонил рекомендацию.
        """
        logger.info("❌ Retrain recommendation dismissed by user")

        ML_RUNTIME_STATE["retrain_recommended"] = False
        ML_RUNTIME_STATE["retrain_recommended_reason"] = None
        ML_RUNTIME_STATE["retrain_candidate_metrics"] = None
        ML_RUNTIME_STATE["retrain_candidate_id"] = None
        ML_RUNTIME_STATE["retrain_candidate_version"] = None
        ML_RUNTIME_STATE["retrain_recommended_at"] = None

        # 🔥 ДОБАВИТЬ: сбрасываем результат обучения
        ML_RUNTIME_STATE["training_completed"] = False
        ML_RUNTIME_STATE["training_result"] = None

        return {
            "status": "dismissed",
            "message": "Retrain recommendation dismissed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_runtime_state(self) -> dict:
        return ML_RUNTIME_STATE




    # ==========================================================
    # STATUS (делегат для router)
    # ==========================================================

    def get_status(self) -> dict:
        """
        Базовый runtime статус.
        Используется для /status
        """

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

        telemetry = self.get_metrics()
        runtime_state = ML_RUNTIME_STATE.copy()

        # Формируем структуру ответа
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "runtime": {
                "ml_model_id": runtime_state.get("ml_model_id"),
                "version": runtime_state.get("version"),
                "model_loaded": runtime_state.get("model_loaded", False),
                "freeze_flag": runtime_state.get("freeze_flag", False),
                "drift_flag": runtime_state.get("drift_flag", False),
                "retrain_requested": runtime_state.get("retrain_requested", False),
            },
            "telemetry": {
                "latency_p95_ms": telemetry.get("latency_p95_ms"),
                "predictions_count": telemetry.get("predictions_count", 0),
                "errors_count": telemetry.get("errors_count", 0),
                "timestamp": telemetry.get("timestamp"),
            },
            "errors": runtime_state.get("errors", []),
            "warnings": runtime_state.get("warnings", []),
        }

    # ==========================================================
    # CLEAR Flag retrain
    # ==========================================================

    def clear_retrain(self) -> dict:
        """
        Сбрасывает флаг retrain_requested.
        """
        ML_RUNTIME_STATE["retrain_requested"] = False

        logger.info("Retrain flag cleared manually")

        return {
            "retrain_requested": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ==========================================================
    # CLEAR TRAINING RESULT
    # ==========================================================

    def clear_training_result(self) -> dict:
        """Очищает результат обучения"""
        ML_RUNTIME_STATE["training_completed"] = False
        ML_RUNTIME_STATE["training_result"] = None

        logger.info("Training result cleared")

        return {
            "status": "cleared",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ==========================================================
    # MODEL TRAINING RESULT
    # ==========================================================


    def get_training_result(self) -> dict:
        """Возвращает результат последнего обучения"""
        return {
            "training_completed": ML_RUNTIME_STATE.get("training_completed", False),
            "training_result": ML_RUNTIME_STATE.get("training_result"),
        }