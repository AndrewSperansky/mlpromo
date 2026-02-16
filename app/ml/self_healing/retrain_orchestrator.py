# app/ml/self_healing/retrain_orchestrator.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any

from app.ml.runtime_state import ML_RUNTIME_STATE
from app.ml.monitoring.retrain_trigger import handle_retrain_if_needed


class RetrainOrchestrator:
    """
    Stage 5.2.1 — Self-Healing Retrain Orchestrator Core

    Responsibilities:
    - checks ML_RUNTIME_STATE retrain flag
    - triggers existing retrain mechanism
    - resets retrain flag
    """

    def process(self) -> Dict[str, Any]:

        # --------------------------------------------------
        # CHECK FLAG
        # --------------------------------------------------

        if not ML_RUNTIME_STATE.get("retrain_requested"):
            return {
                "status": "noop",
                "reason": "retrain_not_requested",
            }

        # --------------------------------------------------
        # BUILD SYNTHETIC ALERT DECISION
        # --------------------------------------------------

        alert_decision = {
            "action": "retrain_recommended",
            "reason": "runtime_self_healing",
        }

        # --------------------------------------------------
        # TRIGGER EXISTING RETRAIN LOGIC
        # --------------------------------------------------

        retrain_result = handle_retrain_if_needed(alert_decision)

        # --------------------------------------------------
        # RESET FLAG
        # --------------------------------------------------

        ML_RUNTIME_STATE["retrain_requested"] = False
        ML_RUNTIME_STATE["last_retrain_ts"] = datetime.now(timezone.utc).isoformat()

        return {
            "status": "triggered",
            "retrain_result": retrain_result,
        }
