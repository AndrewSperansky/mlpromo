# app/ml/model_registry/tradeoff_policy.py
# — LATENCY VS QUALITY TRADEOFF POLICY (Stage 4)

from typing import Dict, Literal


DecisionType = Literal["approve", "reject", "manual_review"]


def decide_tradeoff(
    current_metrics: Dict[str, float],
    candidate_metrics: Dict[str, float],
    slo_config: Dict[str, float],
) -> Dict[str, object]:
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
            "min_quality_gain": float,     # например 0.01 (1%)
            "max_latency_growth": float    # например 0.20 (20%)
        }
    """

    current_rmse = current_metrics["rmse"]
    candidate_rmse = candidate_metrics["rmse"]

    current_latency = current_metrics["latency_p95_ms"]
    candidate_latency = candidate_metrics["latency_p95_ms"]

    latency_slo = slo_config["latency_p95_ms"]
    min_quality_gain = slo_config.get("min_quality_gain", 0.01)
    max_latency_growth = slo_config.get("max_latency_growth", 0.20)

    # ==============================================
    # Compute deltas
    # ==============================================

    quality_delta = (current_rmse - candidate_rmse) / current_rmse
    latency_delta = (candidate_latency - current_latency) / current_latency

    reasons = []

    # ==============================================
    # Rule 1: Hard SLO violation
    # ==============================================

    if candidate_latency > latency_slo:
        return {
            "decision": "reject",
            "reason": "Candidate violates latency SLO",
            "quality_delta": quality_delta,
            "latency_delta": latency_delta,
        }

    # ==============================================
    # Rule 2: Quality regression
    # ==============================================

    if quality_delta <= 0:
        return {
            "decision": "reject",
            "reason": "Candidate quality is worse or equal",
            "quality_delta": quality_delta,
            "latency_delta": latency_delta,
        }

    # ==============================================
    # Rule 3: Acceptable improvement
    # ==============================================

    if (
        quality_delta >= min_quality_gain
        and latency_delta <= max_latency_growth
    ):
        return {
            "decision": "approve",
            "reason": "Quality improved within acceptable latency growth",
            "quality_delta": quality_delta,
            "latency_delta": latency_delta,
        }

    # ==============================================
    # Rule 4: Borderline case
    # ==============================================

    return {
        "decision": "manual_review",
        "reason": "Tradeoff requires human review",
        "quality_delta": quality_delta,
        "latency_delta": latency_delta,
    }
