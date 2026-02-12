# tests/smoke/test_shadow_window.py

from app.ml.monitoring.shadow_latency import evaluate_shadow_latency


def test_shadow_window_approve():
    result = evaluate_shadow_latency(
        inference_metrics={
            "current_latency_series": [100, 105, 110, 95, 102],
            "candidate_latency_series": [108, 112, 115, 100, 109],  # ~ +10%
        },
        slo_config={
            "max_latency_growth": 0.20,
        },
    )

    assert result["decision"] == "approve"


def test_shadow_window_manual_review():
    result = evaluate_shadow_latency(
        inference_metrics={
            "current_latency_series": [100, 100, 100, 100, 100],
            "candidate_latency_series": [130, 130, 130, 130, 130],  # +30%
        },
        slo_config={
            "max_latency_growth": 0.15,  # 15%
        },
    )

    assert result["decision"] == "manual_review"


def test_shadow_window_reject():
    result = evaluate_shadow_latency(
        inference_metrics={
            "current_latency_series": [100, 100, 100, 100, 100],
            "candidate_latency_series": [200, 200, 200, 200, 200],  # +100%
        },
        slo_config={
            "max_latency_growth": 0.20,  # 20%
        },
    )

    assert result["decision"] == "reject"


def test_shadow_window_empty_series():
    result = evaluate_shadow_latency(
        inference_metrics={
            "current_latency_series": [],
            "candidate_latency_series": [],
        },
        slo_config={
            "max_latency_growth": 0.20,
        },
    )

    assert result["decision"] == "manual_review"
    assert result["reason"] == "empty_latency_series"
