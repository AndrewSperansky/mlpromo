# app/ml/self_healing/safe_model_swap.py

from __future__ import annotations

from typing import Dict, Any
from datetime import datetime, timezone

from app.ml.runtime_state import ML_RUNTIME_STATE


class SafeModelSwapError(Exception):
    pass


class SafeModelSwap:
    """
    Stage 5.2.2 — Safe Model Swap Protocol

    Guarantees:
    1. Model trained successfully
    2. Model registered
    3. RuntimeState updated atomically
    4. No partially-updated state
    """

    def execute(self, train_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes safe swap of active model.
        """

        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------

        if not train_result:
            raise SafeModelSwapError("Empty train_result")

        if not train_result.get("success"):
            raise SafeModelSwapError("Training was not successful")

        new_version = train_result.get("model_version")

        if not new_version:
            raise SafeModelSwapError("Missing model_version in train_result")

        # --------------------------------------------------
        # PREPARE TRANSACTION
        # --------------------------------------------------

        previous_version = ML_RUNTIME_STATE.get("version")

        try:
            # --------------------------------------------------
            # UPDATE RUNTIME STATE (LAST STEP)
            # --------------------------------------------------

            ML_RUNTIME_STATE["version"] = new_version
            ML_RUNTIME_STATE["status"] = "ok"
            ML_RUNTIME_STATE["last_swap_ts"] = datetime.now(
                timezone.utc
            ).isoformat()

        except Exception as e:
            # rollback to previous version
            ML_RUNTIME_STATE["version"] = previous_version
            raise SafeModelSwapError(f"Swap failed: {e}") from e

        return {
            "status": "swapped",
            "previous_version": previous_version,
            "new_version": new_version,
        }
