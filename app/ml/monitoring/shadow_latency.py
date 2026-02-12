# app/ml/monitoring/shadow_latency.py
# — SHADOW LATENCY COMPARISON (Stateless, Variant B)



from typing import Dict, Any, List, Optional
import numpy as np


def _calculate_p95(series: List[float]) -> float:
    return float(np.percentile(series, 95))


def evaluate_shadow_latency(
    inference_metrics: Optional[Dict[str, Any]] = None,
    slo_config: Optional[Dict[str, Any]] = None,
    *,
    # --- backward compatibility ---
    current_latency_p95_ms: Optional[float] = None,
    candidate_latency_p95_ms: Optional[float] = None,
    max_allowed_growth: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Shadow latency evaluation.

    Supports:

    Variant A (legacy snapshot mode):
        evaluate_shadow_latency(
            current_latency_p95_ms=...,
            candidate_latency_p95_ms=...,
            max_allowed_growth=...
        )

    Variant B (window mode):
        evaluate_shadow_latency(
            inference_metrics={...},
            slo_config={...}
        )
    """

    # ================================
    # 🅰 LEGACY SNAPSHOT MODE
    # ================================
    if current_latency_p95_ms is not None and candidate_latency_p95_ms is not None:
        current_p95 = current_latency_p95_ms
        candidate_p95 = candidate_latency_p95_ms
        max_growth = max_allowed_growth or 0.1

    # ================================
    # 🅱 NEW MODE (DICT-BASED)
    # ================================
    else:
        inference_metrics = inference_metrics or {}
        slo_config = slo_config or {}

        max_growth = slo_config.get("max_latency_growth", 0.1)

        # Window mode
        if (
            "current_latency_series" in inference_metrics
            and "candidate_latency_series" in inference_metrics
        ):
            current_series = inference_metrics["current_latency_series"]
            candidate_series = inference_metrics["candidate_latency_series"]

            if not current_series or not candidate_series:
                return {
                    "decision": "manual_review",
                    "reason": "empty_latency_series",
                }

            current_p95 = _calculate_p95(current_series)
            candidate_p95 = _calculate_p95(candidate_series)

        # Snapshot mode via dict
        else:
            current_p95 = inference_metrics.get("current_latency_p95_ms")
            candidate_p95 = inference_metrics.get("candidate_latency_p95_ms")

            if current_p95 is None or candidate_p95 is None:
                return {
                    "decision": "manual_review",
                    "reason": "missing_latency_metrics",
                }

    # ================================
    # Evaluation logic
    # ================================
    if current_p95 == 0:
        return {
            "decision": "manual_review",
            "reason": "invalid_current_latency",
        }

    growth = (candidate_p95 - current_p95) / current_p95

    if growth <= max_growth:
        return {
            "decision": "approve",
            "reason": f"shadow_latency_growth_ok ({growth:.2%})",
        }

    if growth <= max_growth * 2:
        return {
            "decision": "manual_review",
            "reason": f"shadow_latency_growth_warning ({growth:.2%})",
        }

    return {
        "decision": "reject",
        "reason": f"shadow_latency_growth_critical ({growth:.2%})",
    }
