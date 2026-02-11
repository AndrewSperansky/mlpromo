# app/ml/monitoring/latency_slo.py
# — LATENCY SLO EVALUATION (DISCRETE PERCENTILE, WINDOWS SAFE)


import os
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone


def _get_metrics_dir() -> Path:
    """
    METRICS_DIR читается в момент вызова
    (test / CI / runtime safe)
    """
    return Path(os.getenv("METRICS_DIR", "metrics"))


def _load_latencies(metrics_file: Path) -> List[float]:
    if not metrics_file.exists():
        return []

    latencies = []

    with open(metrics_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                latency = record.get("latency_ms")
                if latency is not None:
                    latencies.append(float(latency))
            except json.JSONDecodeError:
                continue

    return latencies


# ✨ NEW: стабильный percentile без interpolation
def _discrete_percentile(values: List[float], q: float) -> float:
    """
    Дискретный percentile.
    Подходит для небольших окон и smoke-тестов.
    """
    if not values:
        return 0.0

    values = sorted(values)

    index = int(len(values) * q) - 1
    index = max(0, min(index, len(values) - 1))

    return values[index]


def evaluate_latency_slo(
    p95_threshold_ms: float,
    p99_threshold_ms: float,
) -> Dict[str, Any]:
    """
    Проверка latency SLO:

    - считает p95 / p99
    - определяет breach
    - возвращает structured report
    """

    metrics_dir = _get_metrics_dir()
    metrics_file = metrics_dir / "inference_metrics.jsonl"

    latencies = _load_latencies(metrics_file)

    if not latencies:
        return {
            "status": "no_data",
            "p95": 0.0,
            "p99": 0.0,
            "breached": False,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ✨ UPDATED: используем дискретный percentile
    p95 = _discrete_percentile(latencies, 0.95)
    p99 = _discrete_percentile(latencies, 0.99)

    breached = (
        p95 > p95_threshold_ms
        or p99 > p99_threshold_ms
    )

    return {
        "status": "ok",
        "p95": float(p95),
        "p99": float(p99),
        "breached": breached,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
