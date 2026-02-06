# tests/smoke/test_retrain_policy.py


from app.ml.monitoring.retrain_policy import decide_retrain_action


def test_retrain_policy_actions():
    base = {
        "summary": {
            "shap_drift": False,
            "data_drift": False,
        }
    }

    assert decide_retrain_action(base)["action"] == "none"

    data_only = {
        "summary": {
            "shap_drift": False,
            "data_drift": True,
        }
    }

    assert decide_retrain_action(data_only)["action"] == "monitor"

    shap_only = {
        "summary": {
            "shap_drift": True,
            "data_drift": False,
        }
    }

    assert decide_retrain_action(shap_only)["action"] == "review"

    combined = {
        "summary": {
            "shap_drift": True,
            "data_drift": True,
        }
    }

    assert decide_retrain_action(combined)["action"] == "retrain"
