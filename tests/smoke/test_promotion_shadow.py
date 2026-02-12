# tests/smoke/test_promotion_shadow.py

from app.ml.model_registry.promotion_policy import decide_promotion


def test_promotion_shadow_approve():
    """
    Shadow latency в пределах нормы → promotion approve
    """

    result = decide_promotion(
        current_meta={"rmse": 10.0},
        candidate_meta={"rmse": 9.5},
        inference_metrics={
            "current_latency_p95_ms": 100,
            "candidate_latency_p95_ms": 110,  # +10%
        },
        drift_report={
            "summary": {"shap_drift": False}
        },
        slo_config={
            "latency_p95_ms": 200,
            "min_quality_gain": 0.01,
            "max_latency_growth": 0.15,
        },
    )

    assert result["decision"] == "approve"
    assert result["promote"] is True


def test_promotion_shadow_reject():
    """
    Shadow latency слишком высокая → promotion reject
    """

    result = decide_promotion(
        current_meta={"rmse": 10.0},
        candidate_meta={"rmse": 9.0},
        inference_metrics={
            "current_latency_p95_ms": 100,
            "candidate_latency_p95_ms": 150,  # +50%
        },
        drift_report={
            "summary": {"shap_drift": False}
        },
        slo_config={
            "latency_p95_ms": 300,
            "min_quality_gain": 0.01,
            "max_latency_growth": 0.15,
        },
    )

    assert result["decision"] == "reject"
    assert result["promote"] is False
