# tests/smoke/test_shap_artifacts.py  — SHAP SMOKE TEST


import json
from pathlib import Path


MODELS_DIR = Path("models/_smoke")


def test_shap_summary_smoke():
    """
    Smoke test:
    - shap_summary.json существует
    - не пустой
    - значения > 0
    """

    path = MODELS_DIR / "shap_summary.json"
    assert path.exists(), "shap_summary.json not found"

    with open(path, "r") as f:
        shap_summary = json.load(f)

    assert isinstance(shap_summary, dict)
    assert len(shap_summary) > 0, "shap_summary is empty"

    for feature, value in shap_summary.items():
        assert isinstance(feature, str)
        assert isinstance(value, (int, float))
        assert value >= 0
