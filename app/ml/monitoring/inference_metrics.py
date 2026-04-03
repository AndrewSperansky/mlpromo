# app/ml/monitoring/inference_metrics.py
# — MINIMAL INFERENCE METRICS COLLECTOR


from typing import Dict, Any, List
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import time
import numpy as np

from app.ml.runtime_state import ML_RUNTIME_STATE  # ← добавить


def _get_metrics_dir() -> Path:
    """
    METRICS_DIR читается в runtime
    """
    return Path(os.getenv("METRICS_DIR", "metrics"))


def collect_inference_metrics(
    *,
    ml_model_id: str,
    inputs: np.ndarray,
    outputs: np.ndarray,
    latency_ms: float,
) -> Dict[str, Any]:
    """
    Минимальный сбор inference-метрик.
    """

    metrics_dir = _get_metrics_dir()
    metrics_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "ml_model_id": ml_model_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latency_ms": float(latency_ms),
        "input_shape": list(inputs.shape),
        "output_shape": list(outputs.shape),
        "output_stats": {
            "mean": float(np.mean(outputs)),
            "std": float(np.std(outputs)),
            "min": float(np.min(outputs)),
            "max": float(np.max(outputs)),
        },
    }

    # 🔹 append-only JSONL (production-friendly)
    metrics_path = metrics_dir / "inference_metrics.jsonl"

    with open(metrics_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

        # ===== НОВОЕ: обновляем счётчики в runtime_state =====
        ML_RUNTIME_STATE["predictions_count"] = ML_RUNTIME_STATE.get("predictions_count", 0) + 1

        # Обновляем латентность (скользящее окно для P95)
        if "latencies" not in ML_RUNTIME_STATE:
            ML_RUNTIME_STATE["latencies"] = []

        latencies = ML_RUNTIME_STATE["latencies"]
        latencies.append(latency_ms)

        # Храним последние 100 замеров
        if len(latencies) > 100:
            latencies.pop(0)

        # Пересчитываем P95
        if len(latencies) > 0:
            p95 = np.percentile(latencies, 95)
            ML_RUNTIME_STATE["last_latency_p95"] = float(p95)

        return record

def increment_errors_count() -> None:
    """Увеличивает счётчик ошибок"""
    ML_RUNTIME_STATE["errors_count"] = ML_RUNTIME_STATE.get("errors_count", 0) + 1
