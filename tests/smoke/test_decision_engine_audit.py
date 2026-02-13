# tests/smoke/test_decision_engine_audit.py

import json
from pathlib import Path

from app.ml.decision_engine import DecisionEngine


def test_decision_engine_writes_audit(tmp_path):
    trace_dir = tmp_path / "traces"
    audit_file = tmp_path / "audit.log"

    engine = DecisionEngine(
        trace_output_dir=trace_dir,
        audit_log_path=audit_file,
    )

    trace = engine.evaluate(
        shap_drift_report={"drift_detected": False, "features": {}},
        data_drift_report={"data_drift_detected": False, "features": {}},
        current_metrics={"rmse": 10.0},
        candidate_metrics={"rmse": 9.0},
        slo_config={
            "latency_p95_ms": 500,
            "latency_p99_ms": 800,
            "min_quality_gain": 0.01,
            "max_latency_growth": 0.2,
        },
        candidate_version="v2",
    )

    assert audit_file.exists()

    lines = audit_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 1

    record = json.loads(lines[0])
    assert record["event_type"] == "promotion_decision"
