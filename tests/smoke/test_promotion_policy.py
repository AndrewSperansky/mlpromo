# tests/smoke/test_promotion_policy.py

def test_promotion_policy_smoke():
    from app.ml.model_registry.promotion_policy import decide_promotion

    candidate_metrics = {"rmse": 10.0}
    current_metrics = {"rmse": 12.0}

    result = decide_promotion(candidate_metrics, current_metrics)

    assert result["promote"] is True
    assert "improved" in result["reason"]
