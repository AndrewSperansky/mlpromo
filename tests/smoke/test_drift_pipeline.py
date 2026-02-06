# tests/smoke/test_drift_pipeline.py  — DRIFT + ALERT SMOKE TEST


import numpy as np

from app.ml.monitoring.data_drift_detector import detect_data_drift
from app.ml.monitoring.shap_drift_detector import detect_shap_drift
from app.ml.monitoring.combined_drift_detector import detect_combined_drift
from app.ml.monitoring.alert_engine import decide_action


def test_drift_and_alert_smoke():
    """
    Smoke test:
    - data drift считается
    - shap drift считается
    - combined drift формируется
    - alert action возвращается
    """

    # fake data drift
    reference_data = {
        "price": np.array([100, 110, 120, 130]),
    }
    current_data = {
        "price": np.array([200, 210, 220, 230]),
    }

    data_drift = detect_data_drift(reference_data, current_data)
    assert "data_drift_detected" in data_drift

    # fake shap drift
    shap_ref = {
        "price": 0.3,
        "discount": 0.4,
    }
    shap_curr = {
        "price": 0.6,
        "discount": 0.1,
    }

    shap_drift = detect_shap_drift(shap_ref, shap_curr)
    assert "drift_detected" in shap_drift

    combined = detect_combined_drift(shap_drift, data_drift)
    assert "combined_drift_detected" in combined

    alert = decide_action(combined)
    assert "action" in alert
    assert alert["action"] is not None
