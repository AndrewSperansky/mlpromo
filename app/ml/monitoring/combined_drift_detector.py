# app/ml/monitoring/combined_drift_detector.py
# — COMBINED DRIFT DETECTOR + PIPELINE WRAPPER

from typing import Dict, Any
from pathlib import Path
import json

from app.ml.monitoring.alert_engine import decide_action            # ✨ NEW
from app.ml.monitoring.retrain_trigger import handle_retrain_if_needed  # ✨ NEW


MODELS_DIR = Path("models")


def load_shap_summary() -> Dict[str, float]:
    path = MODELS_DIR / "shap_summary.json"
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def detect_combined_drift(
    shap_drift_report: Dict[str, Any],
    data_drift_report: Dict[str, Any],
) -> Dict[str, Any]:

    combined: Dict[str, Any] = {
        "combined_drift_detected": False,
        "summary": {
            "shap_drift": bool(shap_drift_report.get("drift_detected", False)),
            "data_drift": bool(data_drift_report.get("data_drift_detected", False)),
        },
        "features": {},
    }

    shap_features = shap_drift_report.get("features", {})
    data_features = data_drift_report.get("features", {})

    all_features = set(shap_features) | set(data_features)

    for feature in all_features:
        shap_info = shap_features.get(feature, {})
        data_info = data_features.get(feature, {})

        shap_flag = bool(shap_info.get("drift", False))
        data_status = data_info.get("status")

        combined["features"][feature] = {
            "shap_change_ratio": float(shap_info.get("change_ratio", 0.0)),
            "shap_drift": shap_flag,
            "psi": (
                float(data_info["psi"])
                if "psi" in data_info and data_info["psi"] is not None
                else None
            ),
            "data_drift": data_status,
        }

        if shap_flag or data_status == "drift":
            combined["combined_drift_detected"] = True

    return combined


# ───────────────────────────────────────────────────────────────
# ✨ NEW: High-level pipeline (drift → alert → retrain)
# ───────────────────────────────────────────────────────────────

def run_drift_pipeline(
    shap_drift_report: Dict[str, Any],
    data_drift_report: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Полный pipeline:
    SHAP drift + data drift → combined → alert → retrain trigger
    """

    combined = detect_combined_drift(
        shap_drift_report=shap_drift_report,
        data_drift_report=data_drift_report,
    )

    alert = decide_action(combined)                     # ✨ NEW
    retrain = handle_retrain_if_needed(alert)           # ✨ NEW

    return {
        "combined_drift": combined,
        "alert": alert,
        "retrain": retrain,
    }
