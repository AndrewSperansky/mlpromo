# tests/smoke/test_telemetry.py

from app.ml.telemetry import TelemetryExporter


def test_telemetry_snapshot_smoke():
    exporter = TelemetryExporter()

    snapshot = exporter.collect(
        drift_flag=True,
        latency_p95=123.4,
    )

    assert "timestamp" in snapshot
    assert "active_model_version" in snapshot
    assert snapshot["drift_flag"] is True
    assert snapshot["latency_p95_ms"] == 123.4
    assert "predictions_count" in snapshot
