# app/ml/self_healing/retrain_orchestrator.py
# 5.2.1 Retrain Orchestra Core
# 5.2.4 Anti-Retrain Storm Guard
# 5.2.2 Safe Model Swap Protocol
# 5.2.3 LINEAGE INTEGRATION

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any

from app.ml.runtime_state import ML_RUNTIME_STATE
from app.ml.monitoring.retrain_trigger import handle_retrain_if_needed
from app.ml.self_healing.safe_model_swap import SafeModelSwap, SafeModelSwapError
from app.ml.model_registry.lineage import record_lineage_event


class RetrainOrchestrator:
    """
    Stage 5.2 — Self-Healing Retrain Orchestrator

    Includes:
    - Retrain trigger
    - Anti-Retrain Storm Guard
    - Safe Model Swap Protocol
    - Lineage Integration (5.2.3)
    """

    COOLDOWN_SECONDS = 600  # 10 minutes

    def __init__(self):
        self.swap_protocol = SafeModelSwap()

    def process(self) -> Dict[str, Any]:

        # Проверяем, есть ли новые данные
        # if not self._has_new_data():
        #     return {"status": "noop", "reason": "no_new_data"}

        # --------------------------------------------------
        # CHECK RETRAIN FLAG
        # --------------------------------------------------

        if not ML_RUNTIME_STATE.get("retrain_requested"):
            return {
                "status": "noop",
                "reason": "retrain_not_requested",
            }

        # --------------------------------------------------
        # COOLDOWN
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
        # TRIGGER RETRAIN
        # --------------------------------------------------

        alert_decision = {
            "action": "retrain_recommended",
            "reason": "runtime_self_healing",
        }

        retrain_result = handle_retrain_if_needed(alert_decision)

        if not retrain_result.get("retrain_triggered"):
            ML_RUNTIME_STATE["retrain_requested"] = False
            return {
                "status": "not_triggered",
                "details": retrain_result,
            }

        train_result = retrain_result.get("train_result")

        # --------------------------------------------------
        # SAFE SWAP
        # --------------------------------------------------

        try:
            swap_result = self.swap_protocol.execute(train_result)
        except SafeModelSwapError as e:
            return {
                "status": "swap_failed",
                "error": str(e),
            }

        # --------------------------------------------------
        # LINEAGE INTEGRATION (5.2.3)
        # --------------------------------------------------

        try:
            record_lineage_event(
                event_type="retrain",
                model_id=swap_result.get("new_version"),
                reason=retrain_result.get("reason"),
                metadata={
                    "parent_version": swap_result.get("previous_version"),
                    "trigger": "self_healing",
                },
            )

        except Exception as e:
            # lineage failure не должна ломать runtime
            return {
                "status": "swap_success_lineage_failed",
                "swap_result": swap_result,
                "lineage_error": str(e),
            }

        # --------------------------------------------------
        # FINALIZE STATE
        # --------------------------------------------------

        ML_RUNTIME_STATE["retrain_requested"] = False
        ML_RUNTIME_STATE["last_retrain_ts"] = datetime.now(
            timezone.utc
        ).isoformat()

        return {
            "status": "success",
            "swap_result": swap_result,
        }
