# app/ml/model_registry/tradeoff_policy.py
# — LATENCY vs QUALITY TRADEOFF POLICY

from typing import TypedDict, Literal


class TradeoffResult(TypedDict):
    decision: Literal["approve", "reject", "manual_review"]
    reason: str


def decide_tradeoff(
    current_metrics: dict,
    candidate_metrics: dict,
    slo_config: dict,
) -> TradeoffResult:
    """
    Решает конфликт latency vs quality.

    current_metrics:
        {
            "rmse": float,
            "latency_p95_ms": float
        }

    candidate_metrics:
        {
            "rmse": float,
            "latency_p95_ms": float
        }

    slo_config:
        {
            "latency_p95_ms": float,
            "min_quality_gain": float,
            "max_latency_growth": float
        }
    """

    if not current_metrics:
        return {
            "decision": "approve",
            "reason": "No current model — auto approve",
        }

    rmse_current = current_metrics.get("rmse")
    rmse_candidate = candidate_metrics.get("rmse")

    latency_current = current_metrics.get("latency_p95_ms")
    latency_candidate = candidate_metrics.get("latency_p95_ms")

    if rmse_current is None or rmse_candidate is None:
        return {
            "decision": "manual_review",
            "reason": "Missing RMSE metrics",
        }

    quality_gain = (rmse_current - rmse_candidate) / rmse_current

    min_quality_gain = slo_config.get("min_quality_gain", 0.01)
    max_latency_growth = slo_config.get("max_latency_growth", 0.20)
    latency_slo = slo_config.get("latency_p95_ms")

    latency_growth = 0.0
    if latency_current and latency_candidate:
        latency_growth = (
            latency_candidate - latency_current
        ) / latency_current

    # 🚫 Hard SLO breach
    if latency_slo and latency_candidate and latency_candidate > latency_slo:
        return {
            "decision": "reject",
            "reason": "Latency SLO breached",
        }

    # 🎯 Quality insufficient
    if quality_gain < min_quality_gain:
        return {
            "decision": "manual_review",
            "reason": "Quality gain below threshold",
        }

    # ⚖️ Excessive latency growth
    if latency_growth > max_latency_growth:
        return {
            "decision": "manual_review",
            "reason": "Latency growth too high",
        }

    return {
        "decision": "approve",
        "reason": "Quality improved within latency limits",
    }
