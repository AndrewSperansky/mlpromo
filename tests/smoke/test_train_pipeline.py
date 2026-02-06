#  tests/smoke/test_train_pipeline.py     +  — ПОДДЕРЖКА MODELS_DIR В TRAIN PIPELINE


from pathlib import Path

from app.ml.train.train_pipeline import train_pipeline


MODELS_DIR = Path("models/_smoke")


def test_train_pipeline_smoke():
    """
    Smoke test:
    - train_pipeline выполняется
    - создаются ключевые артефакты
    """

    result = train_pipeline()

    assert result is not None

    assert (MODELS_DIR / "model.cbm").exists(), "model.cbm not created"
    assert (MODELS_DIR / "model.meta.json").exists(), "model.meta.json not created"
    assert (MODELS_DIR / "shap_summary.json").exists(), "shap_summary.json not created"
