


from pathlib import Path
from app.ml.train.train_pipeline import train_pipeline


def test_model_versioning_smoke(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))

    result = train_pipeline(promote=True)

    current = tmp_path / "current"
    archive = tmp_path / "archive"

    assert result["promoted"] is True
    assert (current / "model.cbm").exists()
    assert (current / "model.meta.json").exists()
    assert (current / "shap_summary.json").exists()

    # при первом запуске archive может быть пуст
    assert archive.exists()
