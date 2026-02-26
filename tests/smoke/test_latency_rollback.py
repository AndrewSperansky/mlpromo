# tests/smoke/test_latency_rollback.py
# — SMOKE TEST: LATENCY BREACH → ROLLBACK


import json
from pathlib import Path

from app.ml.monitoring.latency_guard import latency_guard


def test_latency_breach_triggers_rollback(monkeypatch, tmp_path):
    """
    Smoke:
    latency breach → rollback current
    """

    # директории
    models_dir = tmp_path / "models"
    current_dir = models_dir / "current"
    archive_dir = models_dir / "archive" / "v1"

    current_dir.mkdir(parents=True)
    archive_dir.mkdir(parents=True)

    # current (bad)
    (current_dir / "cb_promo_v1.cbm").write_text("bad_model")

    # archive (good)
    (archive_dir / "cb_promo_v1.cbm").write_text("good_model")

    # latency metrics
    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()

    metrics_file = metrics_dir / "inference_metrics.jsonl"
    with open(metrics_file, "w") as f:
        for latency in [200, 220, 250]:
            f.write(json.dumps({"latency_ms": latency}) + "\n")

    monkeypatch.setenv("MODELS_DIR", str(models_dir))
    monkeypatch.setenv("METRICS_DIR", str(metrics_dir))

    result = latency_guard(
        p95_threshold_ms=100,
        p99_threshold_ms=150,
        auto_rollback=True,
    )

    assert result["status"] == "rollback_triggered"
    assert (current_dir / "cb_promo_v1.cbm").read_text() == "good_model"


"""
Что проверяем
✔ latency breach детектится
✔ rollback реально происходит
✔ current заменяется
✔ всё работает без ML / CatBoost
"""