# tests/smoke/test_telemetry.py

from app.ml.telemetry import TelemetryExporter
from app.ml.runtime_state import ML_RUNTIME_STATE


def test_telemetry_snapshot_smoke():

    # ------------------------------------------------------
    # Arrange: обновляем RuntimeState
    # ------------------------------------------------------

    ML_RUNTIME_STATE["version"] = "test-model"
    ML_RUNTIME_STATE["model_loaded"] = True
    ML_RUNTIME_STATE["last_drift_flag"] = True
    ML_RUNTIME_STATE["last_latency_p95"] = 123.4
    ML_RUNTIME_STATE["last_decision"] = "retrain"
    ML_RUNTIME_STATE["retrain_requested"] = True

    exporter = TelemetryExporter()

    # ------------------------------------------------------
    # Act
    # ------------------------------------------------------

    snapshot = exporter.collect()

    # ------------------------------------------------------
    # Assert
    # ------------------------------------------------------

    assert snapshot["active_model_version"] == "test-model"
    assert snapshot["model_loaded"] is True
    assert snapshot["drift_flag"] is True
    assert snapshot["latency_p95_ms"] == 123.4
    assert snapshot["last_decision"] == "retrain"
    assert snapshot["retrain_requested"] is True
