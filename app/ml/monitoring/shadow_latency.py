# app/ml/monitoring/shadow_latency.py
# — SHADOW LATENCY COMPARISON (Stateless, Variant A)

from typing import TypedDict, Literal


class ShadowResult(TypedDict):
    decision: Literal["approve", "reject", "manual_review"]
    reason: str


def evaluate_shadow_latency(
    current_latency_p95_ms: float,
    candidate_latency_p95_ms: float,
    max_allowed_growth: float = 0.15,
) -> ShadowResult:
    """
    Stateless shadow latency comparison.

    max_allowed_growth = 0.15  →  15% допустимый рост
    """

    if current_latency_p95_ms <= 0:
        return {
            "decision": "manual_review",
            "reason": "Invalid current latency value",
        }

    growth = (
        candidate_latency_p95_ms - current_latency_p95_ms
    ) / current_latency_p95_ms

    # ✅ Within allowed growth
    if growth <= max_allowed_growth:
        return {
            "decision": "approve",
            "reason": "Shadow latency within acceptable growth",
        }

    # ⚠ Borderline (до 2x порога)
    if growth <= max_allowed_growth * 2:
        return {
            "decision": "manual_review",
            "reason": "Shadow latency borderline",
        }

    # ❌ Too high
    return {
        "decision": "reject",
        "reason": "Shadow latency too high",
    }
