# app/ml/monitoring/alert_engine.py
# — ALERT ENGINE (DRIFT → ACTION)

from typing import Dict, Any, Literal

from app.ml.monitoring.retrain_policy import decide_retrain_action


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

    # 1️⃣ ML policy decision (внутренняя логика)
    retrain_decision = decide_retrain_action(combined_drift_report)

    shap_drift = combined_drift_report["summary"]["shap_drift"]
    data_drift = combined_drift_report["summary"]["data_drift"]

    action: ActionType
    reason: str
    alert_level: Literal["info", "warning", "critical"]

    # 2️⃣ Governance / business mapping
    if shap_drift and data_drift:
        action = "fallback_to_baseline"
        reason = "SHAP drift and data drift detected"
        alert_level = "critical"

    elif shap_drift:
        action = "retrain_recommended"
        reason = "SHAP drift detected"
        alert_level = "warning"

    elif data_drift:
        action = "warning"
        reason = "Data drift detected"
        alert_level = "warning"

    else:
        action = "no_action"
        reason = "No drift detected"
        alert_level = "info"

    return {
        "action": action,
        "reason": reason,
        "alert_level": alert_level,

        # 🔌 ML policy details (не теряем!)
        "retrain_policy": retrain_decision,

        # 📊 raw drift info
        "drift_summary": combined_drift_report["summary"],
    }
