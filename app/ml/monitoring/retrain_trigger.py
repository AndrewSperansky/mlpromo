# app/ml/monitoring/retrain_trigger.py
# — AUTOMATIC RETRAIN TRIGGER (ALERT → TRAIN)

from typing import Dict, Any
from pathlib import Path
from app.core.settings import settings
from app.ml.train.train_pipeline import train_pipeline


def handle_retrain_if_needed(alert_decision: dict) -> dict:
    if alert_decision.get("action") != "retrain_recommended":
        return {"retrain_triggered": False}

    """
    Запускает retrain в зависимости от решения alert engine.

    Правила:
    - retrain_recommended → обучаем candidate
    - fallback_to_baseline → retrain + НЕ promote
    - остальные → ничего не делаем
    """

    # 🔹 запускаем retrain как candidate
    train_pipeline(promote=False)

    return {
        "retrain_triggered": True,
        "reason": alert_decision.get("reason"),
    }

    # # ✨ NEW: автоматический retrain без активации
    # if action in {"retrain_recommended", "fallback_to_baseline"}:
    #     train_result = train_pipeline(promote=False)
    #
    #     return {
    #         "retrain_triggered": True,
    #         "train_result": train_result,
    #         "reason": alert_decision.get("reason"),
    #     }
    #
    # # ✨ NEW: явный no-op
    # return {
    #     "retrain_triggered": False,
    #     "reason": "No retrain required",
    # }
