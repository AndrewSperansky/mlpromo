# tests/smoke/test_shadow_latency.py

from app.ml.monitoring.shadow_latency import evaluate_shadow_latency


def test_shadow_approve():
    result = evaluate_shadow_latency(
        current_latency_p95_ms=100,
        candidate_latency_p95_ms=110,  # +10%
        max_allowed_growth=0.15,
    )

    assert result["decision"] == "approve"


def test_shadow_manual_review():
    result = evaluate_shadow_latency(
        current_latency_p95_ms=100,
        candidate_latency_p95_ms=125,  # +25%
        max_allowed_growth=0.15,
    )

    assert result["decision"] == "manual_review"


def test_shadow_reject():
    result = evaluate_shadow_latency(
        current_latency_p95_ms=100,
        candidate_latency_p95_ms=150,  # +50%
        max_allowed_growth=0.15,
    )

    assert result["decision"] == "reject"
