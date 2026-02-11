# app/ml/monitoring/latency_slo.py
# — LATENCY SLO (P95 / P99)


from pathlib import Path
from typing import Dict, Any, List
import json
import os
import numpy as np


def _get_metrics_dir() -> Path:
    """
    METRICS_DIR читается в runtime
    """
    return Path(os.getenv("METRICS_DIR", "metrics"))


def _load_latencies() -> List[float]:
    """
    Загружает latency_ms из inference_metrics.jsonl
    """
    metrics_dir = _get_metrics_dir()
    path = metrics_dir / "inference_metrics.jsonl"

    if not path.exists():
        return []

    latencies: List[float] = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if "latency_ms" in record:
                latencies.append(float(record["latency_ms"]))

    return latencies


def evaluate_latency_slo(
    *,
    p95_threshold_ms: float,
    p99_threshold_ms: float,
) -> Dict[str, Any]:
    """
    Проверка latency SLO.

    Возвращает:
    - p95 / p99
    - breach flags
    """

    latencies = _load_latencies()

    if not latencies:
        return {
            "status": "no_data",
            "p95": None,
            "p99": None,
            "breached": False,
        }

    p95 = float(np.percentile(latencies, 95))
    p99 = float(np.percentile(latencies, 99))

    breached = (p95 > p95_threshold_ms) or (p99 > p99_threshold_ms)

    return {
        "status": "ok",
        "p95": p95,
        "p99": p99,
        "thresholds": {
            "p95_ms": p95_threshold_ms,
            "p99_ms": p99_threshold_ms,
        },
        "breached": breached,
    }
