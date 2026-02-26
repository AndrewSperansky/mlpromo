# tests/smoke/test_model_lineage.py
# — SMOKE TEST: MODEL LINEAGE

from pathlib import Path
import json
from app.ml.train.train_pipeline import train_pipeline


def test_model_lineage_smoke(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))

    # первая модель → current
    first = train_pipeline(promote=True, trigger="manual")

    # retrain → candidate
    second = train_pipeline(promote=False, trigger="retrain")

    candidate_meta = tmp_path / "_candidate" / "cb_promo_v1.meta.json"
    assert candidate_meta.exists()

    with open(candidate_meta) as f:
        meta = json.load(f)

    assert meta["parent_model_id"] == first["model_id"]
    assert meta["trigger"] == "retrain"
