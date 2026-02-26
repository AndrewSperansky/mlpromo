
# tests/smoke/test_full_drift_pipeline.py
# — SMOKE TEST: FULL MLOPS LOOP (DRIFT → ALERT → RETRAIN)

from app.ml.monitoring.combined_drift_detector import run_drift_pipeline


def test_full_drift_pipeline_smoke(monkeypatch, tmp_path):
    """
    Smoke test:
    - проходит полный MLOps loop
    - возвращает combined drift
    - возвращает alert
    - запускает retrain (candidate)
    """

    monkeypatch.setenv("MODELS_DIR", str(tmp_path))

    shap_drift_report = {
        "drift_detected": True,
        "features": {
            "price": {
                "drift": True,
                "change_ratio": 0.35,
            }
        },
    }

    data_drift_report = {
        "data_drift_detected": False,
        "features": {
            "price": {
                "status": "stable",
                "psi": 0.05,
            }
        },
    }

    result = run_drift_pipeline(
        shap_drift_report=shap_drift_report,
        data_drift_report=data_drift_report,
    )

    assert "combined_drift" in result
    assert "alert" in result
    assert "retrain" in result

    assert result["alert"]["action"] == "retrain_recommended"
    assert result["retrain"]["retrain_triggered"] is True

    assert (tmp_path / "_candidate" / "cb_promo_v1.cbm").exists()
