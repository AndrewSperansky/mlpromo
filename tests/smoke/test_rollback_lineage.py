# tests/smoke/test_rollback_lineage.py

from app.ml.model_registry.rollback import rollback_current_to_archive
import json
import os


def test_rollback_creates_lineage_event(tmp_path, monkeypatch):
    """
    Smoke: rollback создаёт lineage event.
    """

    # Подменяем MODELS_DIR
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))

    models_dir = tmp_path
    archive_dir = models_dir / "archive"
    current_dir = models_dir / "current"

    archive_dir.mkdir(parents=True)
    current_dir.mkdir(parents=True)

    # Создаём fake archived model
    archived_model_dir = archive_dir / "test_model_1"
    archived_model_dir.mkdir()

    meta = {
        "model_id": "test_model_1"
    }

    with open(archived_model_dir / "cb_promo_v1.meta.json", "w") as f:
        json.dump(meta, f)

    # Выполняем rollback
    result = rollback_current_to_archive()

    assert result["rollback_performed"] is True

    # Проверяем lineage events
    lineage_file = models_dir / "history" / "lineage_events.json"

    assert lineage_file.exists()

    data = json.loads(lineage_file.read_text())

    assert any(e["event_type"] == "rollback" for e in data)

    alerts_file = models_dir / "history" / "alerts.json"
    assert alerts_file.exists()

    alerts = json.loads(alerts_file.read_text())
    assert any(a["alert_type"] == "model_rollback" for a in alerts)