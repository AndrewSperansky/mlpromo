# app/ml/contract_check.py
from pathlib import Path
from typing import Any, Dict

from app.core.settings import settings
from app.ml.model_loader import ModelLoader


def check_ml_contract() -> Dict[str, Any]:
    """
    Проверяет корректность ML-контракта при старте сервиса.
    НЕ бросает исключений.
    """

    result = {
        "status": "ok",
        "model_loaded": False,
        "errors": [],
        "warnings": [],
        "model_path": settings.MODEL_PATH,
    }

    model_path = Path(settings.MODEL_PATH)

    if not model_path.exists():
        result["status"] = "degraded"
        result["errors"].append(f"Model file not found: {model_path}")
        return result

    try:
        model, meta = ModelLoader.load()

        if model is None:
            result["status"] = "degraded"
            result["errors"].append("ModelLoader returned model=None")
            return result

        if not isinstance(meta, dict):
            result["status"] = "degraded"
            result["errors"].append("Model meta is not a dict")
            return result

        if "feature_order" not in meta or not meta["feature_order"]:
            result["status"] = "degraded"
            result["errors"].append("meta.feature_order is missing or empty")

        result["model_loaded"] = True

    except Exception as exc:
        result["status"] = "degraded"
        result["errors"].append(str(exc))

    return result
