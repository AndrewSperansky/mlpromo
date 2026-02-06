# app/ml/monitoring/data_drift_detector.py
# — DATA DRIFT DETECTOR (PSI)


from typing import Dict
import numpy as np


# === НАСТРОЙКИ =====================================================

PSI_BUCKETS = 10

# Пороги PSI
PSI_WARNING = 0.1
PSI_DRIFT = 0.25


# === CORE ==========================================================

def _psi(expected: np.ndarray, actual: np.ndarray) -> float:
    """
    Population Stability Index
    """
    breakpoints = np.linspace(0, 100, PSI_BUCKETS + 1)

    expected_perc = np.percentile(expected, breakpoints)
    actual_perc = np.percentile(actual, breakpoints)

    psi_value = 0.0

    for i in range(len(expected_perc) - 1):
        expected_ratio = (
            (expected >= expected_perc[i]) &
            (expected < expected_perc[i + 1])
        ).mean()

        actual_ratio = (
            (actual >= actual_perc[i]) &
            (actual < actual_perc[i + 1])
        ).mean()

        if expected_ratio == 0 or actual_ratio == 0:
            continue

        psi_value += (actual_ratio - expected_ratio) * np.log(
            actual_ratio / expected_ratio
        )

    return round(float(psi_value), 4)


def detect_data_drift(
    reference_data: Dict[str, np.ndarray],
    current_data: Dict[str, np.ndarray],
) -> Dict:
    """
    Считает data drift по всем числовым фичам
    """
    report = {
        "data_drift_detected": False,
        "features": {},
    }

    for feature, ref_values in reference_data.items():
        curr_values = current_data.get(feature)

        if curr_values is None:
            continue

        psi_value = _psi(ref_values, curr_values)

        status = "ok"
        if psi_value >= PSI_DRIFT:
            status = "drift"
            report["data_drift_detected"] = True
        elif psi_value >= PSI_WARNING:
            status = "warning"

        report["features"][feature] = {
            "psi": psi_value,
            "status": status,
        }

    return report
