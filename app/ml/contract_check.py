# app/ml/contract_check.py

import pandas as pd
from pathlib import Path
from app.core.settings import settings
from app.ml.runtime_state import ML_RUNTIME_STATE


# ==============================
# CSV CONTRACT VALIDATION
# ==============================

REQUIRED_COLUMNS = [
    "PromoID",
    "SKU",
    "StoreID",
    "Date",
    "SalesQty_Promo",
]


def validate_industrial_contract(df: pd.DataFrame):
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df["SalesQty_Promo"].isnull().any():
        raise ValueError("Target column SalesQty_Promo contains NULL values")

    return True


# ==============================
# RUNTIME CONTRACT CHECK
# ==============================

def check_ml_contract() -> dict:
    """
    Проверяет корректность ML-контракта при старте сервиса.
    НЕ бросает исключений.
    """

    errors = []
    warnings = []

    model_id = ML_RUNTIME_STATE.get("ml_model_id")

    if not model_id:
        return {
            "checked": True,
            "status": "degraded",
            "model_loaded": False,
            "errors": ["No active model in runtime state"],
            "warnings": [],
        }

    model_path = Path(settings.ML_MODEL_DIR) / "current" / f"{model_id}.cbm"

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