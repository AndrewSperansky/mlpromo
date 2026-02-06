# app/api/v1/ml/train_model.py

#  ===========  Stage 3  ====================

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
import json


# === НАСТРОЙКИ =====================================================

MODEL_NAME = "promo_uplift"
MODELS_ROOT = Path("models") / MODEL_NAME
TOP_K_FEATURES = 5


# === TRAIN (TRIGGER) ===============================================

def train() -> dict:
    """
    API-триггер обучения модели
    Реальная логика — в ML pipeline
    """
    return {
        "status": "train_triggered",
        "triggered_at": datetime.now(timezone.utc).isoformat(),
    }


# === EXPLAIN =======================================================

def explain(
    features: Dict[str, Any],
    model_version: str,
) -> List[Dict[str, float]]:
    """
    Возвращает объяснение модели на основе SHAP summary
    (без вычисления SHAP в runtime)
    """

    shap_summary_path = (
        MODELS_ROOT / model_version / "shap_summary.json"
    )

    # fallback: нет SHAP
    if not shap_summary_path.exists():
        return _fallback_explain(features)

    with open(shap_summary_path, "r") as f:
        shap_summary = json.load(f)

    # сортируем по важности
    sorted_features = sorted(
        shap_summary.items(),
        key=lambda x: abs(x[1]),
        reverse=True,
    )

    response = []
    for feature, importance in sorted_features[:TOP_K_FEATURES]:
        response.append(
            {
                "feature": feature,
                "importance": float(importance),
            }
        )

    return response


# === FALLBACK ======================================================

def _fallback_explain(
    features: Dict[str, Any]
) -> List[Dict[str, float]]:
    """
    Безопасный fallback, если SHAP недоступен
    """
    response = []

    for k, v in features.items():
        response.append(
            {
                "feature": k,
                "importance": float(v)
                if isinstance(v, (int, float))
                else 0.0,
            }
        )

    return response[:TOP_K_FEATURES]
