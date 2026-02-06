# tests/smoke/conftest.py


import pytest
from pathlib import Path
import os

from app.ml.train.train_pipeline import train_pipeline


SMOKE_MODELS_DIR = Path("models/_smoke")


@pytest.fixture(scope="session", autouse=True)
def ensure_smoke_model_and_shap_exist():
    """
    Session-level setup for smoke tests:
    - перенаправляет MODELS_DIR в models/_smoke
    - обучает модель один раз
    - гарантирует наличие SHAP артефактов
    """

    # сохраняем старое значение, если было
    old_models_dir = os.environ.get("MODELS_DIR")

    os.environ["MODELS_DIR"] = str(SMOKE_MODELS_DIR)

    SMOKE_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    train_pipeline()

    assert (SMOKE_MODELS_DIR / "model.cbm").exists()
    assert (SMOKE_MODELS_DIR / "shap_summary.json").exists()

    yield

    # аккуратно восстанавливаем окружение
    if old_models_dir is not None:
        os.environ["MODELS_DIR"] = old_models_dir
    else:
        os.environ.pop("MODELS_DIR", None)
