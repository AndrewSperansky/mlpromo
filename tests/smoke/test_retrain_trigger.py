# tests/smoke/test_retrain_trigger.py

from app.ml.monitoring.retrain_trigger import handle_retrain_if_needed


def test_retrain_trigger_smoke(monkeypatch, tmp_path):
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))

    alert_decision = {
        "action": "retrain_recommended",
        "reason": "SHAP drift detected",
    }

    result = handle_retrain_if_needed(alert_decision)

    assert result["retrain_triggered"] is True
    assert (tmp_path / "_candidate" / "model.cbm").exists()
    assert (tmp_path / "current").exists()
