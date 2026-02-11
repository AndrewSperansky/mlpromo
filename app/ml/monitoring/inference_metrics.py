# app/ml/monitoring/inference_metrics.py
# — MINIMAL INFERENCE METRICS COLLECTOR


from typing import Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import time
import numpy as np


def _get_metrics_dir() -> Path:
    """
    METRICS_DIR читается в runtime
    (test / CI / prod safe)
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

    Что фиксируем:
    - ml_model_id
    - timestamp
    - latency
    - input / output shape
    - базовую статистику выходов
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

    return record
