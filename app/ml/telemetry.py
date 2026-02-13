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

    def collect(
        self,
        *,
        drift_flag: bool = False,
        latency_p95: float | None = None,
    ) -> Dict[str, Any]:

        # --------------------------------------------------
        # SAFE INFERENCE METRICS ACCESS
        # --------------------------------------------------

        predictions_count = 0
        errors_count = 0

        # inference_metrics реализован как module-level state
        if hasattr(inference_metrics, "INFERENCE_METRICS"):
            metrics = getattr(inference_metrics, "INFERENCE_METRICS")

            predictions_count = metrics.get("predictions_count", 0)
            errors_count = metrics.get("errors_count", 0)

        # --------------------------------------------------
        # BUILD SNAPSHOT
        # --------------------------------------------------

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),

            # Model state
            "active_model_version": ML_RUNTIME_STATE.get("version"),
            "model_loaded": ML_RUNTIME_STATE.get("model_loaded", False),

            # Runtime flags
            "drift_flag": drift_flag,
            "freeze_flag": ML_RUNTIME_STATE.get("status") == "frozen",

            # Latency
            "latency_p95_ms": latency_p95,

            # Counters
            "predictions_count": predictions_count,
            "errors_count": errors_count,
        }
