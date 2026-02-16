# app/ml/monitoring/retrain_trigger.py
# — AUTOMATIC RETRAIN TRIGGER (ALERT → TRAIN)

from typing import Dict, Any
from app.ml.train.train_pipeline import train_pipeline


def handle_retrain_if_needed(alert_decision: dict) -> dict:
    """
    Запускает retrain в зависимости от решения alert engine.

    Правила:
    - retrain_recommended → обучаем candidate
    - fallback_to_baseline → retrain + НЕ promote
    - остальные → ничего не делаем

    Stage 5.2.2 — Extended for Safe Model Swap Protocol:
    - Возвращает train_result для transactional swap
    """

    action = alert_decision.get("action")

    if action != "retrain_recommended":
        return {
            "retrain_triggered": False,
            "reason": alert_decision.get("reason"),
        }

    # --------------------------------------------------
    # RUN TRAIN PIPELINE (candidate only)
    # --------------------------------------------------

    train_result = train_pipeline(promote=False)

    # --------------------------------------------------
    # NORMALIZE TRAIN RESULT (safety layer)
    # --------------------------------------------------

    # train_pipeline в smoke может возвращать разные структуры,
    # поэтому мягко нормализуем для SafeModelSwap

    normalized_result: Dict[str, Any] = {
        "success": bool(train_result),
        "model_version": None,
    }

    if isinstance(train_result, dict):
        normalized_result["success"] = train_result.get("success", True)
        normalized_result["model_version"] = train_result.get("model_version")

    return {
        "retrain_triggered": True,
        "reason": alert_decision.get("reason"),
        "train_result": normalized_result,
    }
