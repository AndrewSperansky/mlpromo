#  app/ml/monitoring/alert_engine.py
#  — ALERT ENGINE (DRIFT → ACTION)


from typing import Dict, Any, Literal


ActionType = Literal[
    "no_action",
    "log_only",
    "warning",
    "retrain_recommended",
    "fallback_to_baseline",
]


def decide_action(
    combined_drift_report: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Преобразует drift-сигнал в управленческое действие
    """

    shap_drift = combined_drift_report["summary"]["shap_drift"]
    data_drift = combined_drift_report["summary"]["data_drift"]

    action: ActionType
    reason: str

    if shap_drift and data_drift:
        action = "fallback_to_baseline"
        reason = "SHAP drift and data drift detected"
    elif shap_drift:
        action = "retrain_recommended"
        reason = "SHAP drift detected"
    elif data_drift:
        action = "warning"
        reason = "Data drift detected"
    else:
        action = "no_action"
        reason = "No drift detected"

    return {
        "action": action,
        "reason": reason,
        "drift_summary": combined_drift_report["summary"],
    }
