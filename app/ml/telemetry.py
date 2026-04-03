# app/ml/telemetry.py

from __future__ import annotations

from typing import Dict, Any
from datetime import datetime, timezone

from app.ml.runtime_state import ML_RUNTIME_STATE

# ⚠ аккуратно импортируем модуль, а не функцию
import app.ml.monitoring.inference_metrics as inference_metrics


class TelemetryExporter:
    """
    Stage 5 — Runtime Telemetry Snapshot

    Возвращает JSON-метрики для:
    - API /metrics
    - Monitoring
    """

    def collect(self) -> Dict[str, Any]:

        # --------------------------------------------------
        # SAFE INFERENCE METRICS ACCESS
        # --------------------------------------------------

        # predictions_count = 0
        # errors_count = 0

        # inference_metrics реализован как module-level state
        # if hasattr(inference_metrics, "INFERENCE_METRICS"):
        #     metrics = getattr(inference_metrics, "INFERENCE_METRICS")
        #
        #     predictions_count = metrics.get("predictions_count", 0)
        #     errors_count = metrics.get("errors_count", 0)

        # --------------------------------------------------
        # BUILD SNAPSHOT
        # --------------------------------------------------

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),

            # Model state
            "active_model_version": ML_RUNTIME_STATE.get("version"),
            "model_loaded": ML_RUNTIME_STATE.get("model_loaded", False),

            # Runtime flags (updated by DecisionEngine)
            "drift_flag": ML_RUNTIME_STATE.get("last_drift_flag", False),
            "freeze_flag": ML_RUNTIME_STATE.get("status") == "frozen",
            "latency_p95_ms": ML_RUNTIME_STATE.get("last_latency_p95"),

            "last_decision": ML_RUNTIME_STATE.get("last_decision"),
            "retrain_requested": ML_RUNTIME_STATE.get("retrain_requested", False),

            # Counters
            "predictions_count": ML_RUNTIME_STATE.get("predictions_count", 0),
            "errors_count": ML_RUNTIME_STATE.get("errors_count", 0),
        }
