# tests/smoke/test_promotion_policy_v2.py


from app.ml.model_registry.promotion_policy import decide_promotion


def test_promotion_approve():
    result = decide_promotion(
        current_meta={"rmse": 10.0},
        candidate_meta={"rmse": 9.8},
        inference_metrics={
            "current_latency_p95_ms": 80,
            "candidate_latency_p95_ms": 85,
        },
        drift_report={
            "summary": {"shap_drift": False}
        },
        slo_config={
            "latency_p95_ms": 100,
            "min_quality_gain": 0.01,
            "max_latency_growth": 0.20,
        },
    )

    assert result["decision"] == "approve"


def test_promotion_reject_drift():
    result = decide_promotion(
        current_meta={"rmse": 10.0},
        candidate_meta={"rmse": 9.5},
        inference_metrics={
            "current_latency_p95_ms": 80,
            "candidate_latency_p95_ms": 85,
        },
        drift_report={
            "summary": {"shap_drift": True}
        },
        slo_config={"latency_p95_ms": 100},
    )

    assert result["decision"] == "reject"


def test_promotion_manual_review():
    result = decide_promotion(
        current_meta={"rmse": 10.0},
        candidate_meta={"rmse": 9.95},
        inference_metrics={
            "current_latency_p95_ms": 80,
            "candidate_latency_p95_ms": 110,
        },
        drift_report={
            "summary": {"shap_drift": False}
        },
        slo_config={
            "latency_p95_ms": 120,
            "min_quality_gain": 0.05,
            "max_latency_growth": 0.05,
        },
    )

    assert result["decision"] == "reject"
