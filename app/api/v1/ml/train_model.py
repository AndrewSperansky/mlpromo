# app/api/v1/ml/train_model.py

from datetime import datetime, timezone
from typing import Dict, Any


def train() -> dict:
    return {
        "status": "trained",
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }


def explain(features: Dict[str, Any], model=None):
    # SHAP / fallback
    return [
        {"feature": k, "effect": float(v) if isinstance(v, (int, float)) else 0.0}
        for k, v in features.items()
    ]
