# app/ml/monitoring/alert_engine.py
# — ALERT ENGINE (DRIFT → ACTION + SYSTEM ALERTS)

from typing import Dict, Any, Literal
from datetime import datetime, timezone
from pathlib import Path
import json
import os

from app.ml.monitoring.retrain_policy import decide_retrain_action


# ==========================================================
# Drift → Governance Decision (уже существующая логика)
# ==========================================================

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

    retrain_decision = decide_retrain_action(combined_drift_report)

    shap_drift = combined_drift_report["summary"]["shap_drift"]
    data_drift = combined_drift_report["summary"]["data_drift"]

    action: ActionType
    reason: str
    alert_level: Literal["info", "warning", "critical"]

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
        "retrain_policy": retrain_decision,
        "drift_summary": combined_drift_report["summary"],
    }


# ==========================================================
# Stage 4 — Runtime Alert Logger (system-level events)
# ==========================================================

def _get_alerts_file() -> Path:
    """
    Возвращает путь к alerts.json
    """
    models_dir = Path(os.getenv("MODELS_DIR", "models"))
    history_dir = models_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    return history_dir / "alerts.json"


def trigger_alert(
    alert_type: str,
    severity: Literal["info", "warning", "critical"],
    payload: Dict[str, Any] | None = None,
) -> None:
    """
    Логирует системный alert (rollback, latency breach и т.д.)
    """

    alerts_file = _get_alerts_file()

    if alerts_file.exists():
        with open(alerts_file, "r") as f:
            alerts = json.load(f)
    else:
        alerts = []

    alert_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_type": alert_type,
        "severity": severity,
        "payload": payload or {},
    }

    alerts.append(alert_event)

    with open(alerts_file, "w") as f:
        json.dump(alerts, f, indent=2)
