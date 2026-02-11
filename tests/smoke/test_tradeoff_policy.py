#  tests/smoke/test_tradeoff_policy.py

from app.ml.model_registry.tradeoff_policy import decide_tradeoff


def test_tradeoff_approve():
    result = decide_tradeoff(
        current_metrics={"rmse": 10.0, "latency_p95_ms": 80},
        candidate_metrics={"rmse": 9.8, "latency_p95_ms": 85},
        slo_config={
            "latency_p95_ms": 100,
            "min_quality_gain": 0.01,
            "max_latency_growth": 0.20,
        },
    )

    assert result["decision"] == "approve"


def test_tradeoff_reject_latency():
    result = decide_tradeoff(
        current_metrics={"rmse": 10.0, "latency_p95_ms": 80},
        candidate_metrics={"rmse": 9.7, "latency_p95_ms": 150},
        slo_config={"latency_p95_ms": 100},
    )

    assert result["decision"] == "reject"


def test_tradeoff_manual_review():
    result = decide_tradeoff(
        current_metrics={"rmse": 10.0, "latency_p95_ms": 80},
        candidate_metrics={"rmse": 9.9, "latency_p95_ms": 110},
        slo_config={
            "latency_p95_ms": 120,
            "min_quality_gain": 0.05,
            "max_latency_growth": 0.10,
        },
    )

    assert result["decision"] == "manual_review"
