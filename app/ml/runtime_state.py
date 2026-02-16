# app/ml/runtime_state.py

from datetime import datetime, timezone
from typing import Any, Dict


ML_RUNTIME_STATE: Dict[str, Any] = {
    # --- базовое состояние ---
    "status": "ok",
    "model_loaded": False,
    "version": None,
    "errors": [],
    "warnings": [],

    # --- Stage 5 control-plane ---
    "last_drift_flag": False,
    "last_latency_p95": None,
    "last_decision": None,
    "last_decision_timestamp": None,
    "retrain_requested": False,
   }


def update_runtime_state(**kwargs) -> None:
    """
    Controlled runtime state update helper.
    """

    for key, value in kwargs.items():
        if key in ML_RUNTIME_STATE:
            ML_RUNTIME_STATE[key] = value

    ML_RUNTIME_STATE["last_update_ts"] = datetime.now(timezone.utc).isoformat()
