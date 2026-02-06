#  app/ml/monitoring/shap_drift_detector.py


from pathlib import Path
import json
from typing import Dict


# === НАСТРОЙКИ =====================================================

MODEL_NAME = "promo_uplift"
MODELS_ROOT = Path("models") / MODEL_NAME

# Порог изменения важности SHAP (30% = сигнал drift)
SHAP_DRIFT_THRESHOLD = 0.30


# === CORE ==========================================================

def load_shap_summary(model_version: str) -> Dict[str, float]:
    path = MODELS_ROOT / model_version / "shap_summary.json"
    if not path.exists():
        raise FileNotFoundError(f"shap_summary.json not found for {model_version}")

    with open(path, "r") as f:
        return json.load(f)


def detect_shap_drift(
    reference_summary: Dict[str, float],
    current_summary: Dict[str, float],
) -> Dict:
    """
    Сравнивает SHAP summary двух версий модели
    """
    drift_report = {
        "drift_detected": False,
        "features": {},
    }

    for feature, ref_value in reference_summary.items():
        curr_value = current_summary.get(feature, 0.0)

        if ref_value == 0:
            change_ratio = 0.0
        else:
            change_ratio = abs(curr_value - ref_value) / abs(ref_value)

        drift_report["features"][feature] = {
            "reference": ref_value,
            "current": curr_value,
            "change_ratio": round(change_ratio, 3),
            "drift": change_ratio >= SHAP_DRIFT_THRESHOLD,
        }

        if change_ratio >= SHAP_DRIFT_THRESHOLD:
            drift_report["drift_detected"] = True

    return drift_report


def save_drift_report(
    report: Dict,
    model_version: str,
):
    output_path = (
        MODELS_ROOT / model_version / "shap_drift_report.json"
    )

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
