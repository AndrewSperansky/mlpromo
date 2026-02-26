# tests/smoke/test_rollback.py
# — SMOKE TEST: MODEL ROLLBACK

from pathlib import Path
import json
from app.ml.model_registry.rollback import rollback_current_to_archive


def test_model_rollback_smoke(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))

    models_dir = tmp_path
    current = models_dir / "current"
    archive = models_dir / "archive"

    # ✨ NEW: подготавливаем archive
    archived_model = archive / "model_v1"
    archived_model.mkdir(parents=True)

    (archived_model / "cb_promo_v1.cbm").write_text("dummy model")
    (archived_model / "shap_summary.json").write_text("{}")

    meta = {
        "model_id": "model_v1",
        "stage": "archived",
    }

    with open(archived_model / "cb_promo_v1.meta.json", "w") as f:
        json.dump(meta, f)

    # ✨ NEW: подготавливаем current
    current.mkdir()
    (current / "cb_promo_v1.cbm").write_text("bad model")

    # 🔁 rollback
    result = rollback_current_to_archive()

    assert result["rollback_performed"] is True
    assert (current / "cb_promo_v1.cbm").exists()
    assert (current / "cb_promo_v1.meta.json").exists()

    with open(current / "cb_promo_v1.meta.json") as f:
        restored_meta = json.load(f)

    assert restored_meta["rolled_back_from"] == "model_v1"
