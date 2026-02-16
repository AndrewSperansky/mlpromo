# app/ml/self_healing/retrain_orchestrator.py
# 5.2.1 Retrain Orchestra Core
# 5.2.4 Anti-Retrain Storm Guard


from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any

from app.ml.runtime_state import ML_RUNTIME_STATE
from app.ml.monitoring.retrain_trigger import handle_retrain_if_needed


class RetrainOrchestrator:
    """
    Stage 5.2.2 — Self-Healing Retrain Orchestrator
    + Cooldown protection
    """

    # 🔹 минимальный интервал между retrain (в секундах)
    COOLDOWN_SECONDS = 600  # 10 минут

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
        # COOLDOWN CHECK
        # --------------------------------------------------

        last_retrain_ts = ML_RUNTIME_STATE.get("last_retrain_ts")

        if last_retrain_ts:
            last_dt = datetime.fromisoformat(last_retrain_ts)
            now = datetime.now(timezone.utc)

            elapsed = (now - last_dt).total_seconds()

            if elapsed < self.COOLDOWN_SECONDS:
                return {
                    "status": "cooldown_active",
                    "seconds_remaining": int(self.COOLDOWN_SECONDS - elapsed),
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
