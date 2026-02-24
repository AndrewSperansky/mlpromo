# app/ml/contract_check.py

from pathlib import Path
from typing import Any, Dict

from app.core.settings import settings
from app.ml.runtime_state import ML_RUNTIME_STATE


def check_ml_contract() -> dict:
    """
    Проверяет корректность ML-контракта при старте сервиса.
    НЕ бросает исключений.
    """
    errors = []
    warnings = []

    model_id = ML_RUNTIME_STATE.get("ml_model_id")
    model_path = Path(settings.ML_MODEL_DIR) / f"{model_id}.cbm"

    if not model_path.exists():
        errors.append(f"Model file not found: {model_path}")

    status = "ok" if not errors else "degraded"

    return {
        "checked": True,
        "status": status,
        "model_loaded": False if errors else True,
        "errors": errors,
        "warnings": warnings,
        "model_path": str(model_path),
    }
