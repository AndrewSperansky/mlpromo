#  app/ml/train/shap_utils.py


import json
from pathlib import Path
import numpy as np
import shap


def compute_shap_catboost(model, X):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    expected_value = explainer.expected_value
    return shap_values, expected_value


def save_shap_artifacts(
    shap_values,
    expected_value,
    feature_names,
    models_dir: Path,
):
    models_dir.mkdir(parents=True, exist_ok=True)

    np.save(models_dir / "shap_values.npy", shap_values)

    with open(models_dir / "shap_expected_value.json", "w") as f:
        json.dump(
            {"expected_value": float(expected_value)},
            f,
            indent=2,
        )

    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)

    shap_summary = {
        feature: float(value)
        for feature, value in zip(feature_names, mean_abs_shap)
    }

    with open(models_dir / "shap_summary.json", "w") as f:
        json.dump(shap_summary, f, indent=2)
