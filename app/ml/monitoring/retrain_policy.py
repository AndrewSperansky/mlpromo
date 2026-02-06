#  app/ml/monitoring/retrain_policy.py
#  — ПОЛИТИКА ПЕРЕОБУЧЕНИЯ


from typing import Dict, Any
from datetime import datetime, timezone


def decide_retrain_action(
    combined_drift_report: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Определяет действие по результатам drift-мониторинга
    """

    shap_drift = combined_drift_report["summary"].get("shap_drift", False)
    data_drift = combined_drift_report["summary"].get("data_drift", False)

    action = "none"
    reason = "no_drift"

    if data_drift and not shap_drift:
        action = "monitor"
        reason = "data_drift_only"

    if shap_drift and not data_drift:
        action = "review"
        reason = "shap_drift_only"

    if shap_drift and data_drift:
        action = "retrain"
        reason = "combined_drift"

    return {
        "action": action,
        "reason": reason,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
