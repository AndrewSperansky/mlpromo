# app/ml/train/train_pipeline.py


from pathlib import Path
from datetime import datetime, timezone
import json
import os
import pandas as pd
from catboost import CatBoostRegressor

from app.ml.train.shap_utils import (
    compute_shap_catboost,
    save_shap_artifacts,
)

from models.model_manager import promote_candidate


BASE_MODELS_DIR = Path(os.getenv("MODELS_DIR", "models"))
CANDIDATE_DIR = BASE_MODELS_DIR / "_candidate"


def _prepare_training_data():
    data = pd.DataFrame(
        {
            "price": [100, 120, 90, 110],
            "discount": [10, 20, 0, 15],
            "avg_sales_7d": [30, 25, 40, 28],
            "promo_days_left": [5, 3, 10, 2],
            "target": [140, 160, 135, 150],
        }
    )

    X = data.drop(columns=["target"])
    y = data["target"]
    return X, y


def train_pipeline(promote: bool = False) -> dict:
    """
    Train model and produce candidate artifacts.
    promote=True → делает модель активной
    """

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)

    X_train, y_train = _prepare_training_data()
    feature_names = X_train.columns.tolist()

    model = CatBoostRegressor(
        iterations=200,
        depth=6,
        learning_rate=0.05,
        loss_function="RMSE",
        random_seed=42,
        verbose=False,
    )

    model.fit(X_train, y_train)

    model_path = CANDIDATE_DIR / "model.cbm"
    model.save_model(str(model_path))

    shap_values, expected_value = compute_shap_catboost(
        model=model,
        X=X_train,
    )

    save_shap_artifacts(
        shap_values=shap_values,
        expected_value=expected_value,
        feature_names=feature_names,
        models_dir=CANDIDATE_DIR,
    )

    meta = {
        "model_name": "promo_uplift",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "features": feature_names,
        "status": "candidate",
        "artifacts": {
            "model": "model.cbm",
            "shap_summary": "shap_summary.json",
        },
    }

    with open(CANDIDATE_DIR / "model.meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    if promote:
        promote_candidate(CANDIDATE_DIR)

    return {
        "status": "trained",
        "promoted": promote,
        "candidate_dir": str(CANDIDATE_DIR),
    }
