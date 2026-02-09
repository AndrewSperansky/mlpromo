# app/ml/train/train_pipeline.py
# — TRAIN PIPELINE WITH VERSIONING SUPPORT (FIXED ARCHIVE CONTRACT)

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


def _get_models_dir() -> Path:
    """
    MODELS_DIR читается в момент вызова
    (test / CI / runtime safe)
    """
    return Path(os.getenv("MODELS_DIR", "models"))


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
    promote=False → candidate
    promote=True  → current + archive previous
    """

    MODELS_DIR = _get_models_dir()

    candidate_dir = MODELS_DIR / "_candidate"
    current_dir = MODELS_DIR / "current"
    archive_dir = MODELS_DIR / "archive"

    # 🟨 ВСЕ инфраструктурные директории создаём всегда
    candidate_dir.mkdir(parents=True, exist_ok=True)
    current_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

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

    model_path = candidate_dir / "model.cbm"
    model.save_model(str(model_path))

    shap_values, expected_value = compute_shap_catboost(
        model=model,
        X=X_train,
    )

    save_shap_artifacts(
        shap_values=shap_values,
        expected_value=expected_value,
        feature_names=feature_names,
        models_dir=candidate_dir,
    )

    meta = {
        "model_name": "promo_uplift",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "features": feature_names,
        "artifacts": {
            "model": "model.cbm",
            "shap_summary": "shap_summary.json",
        },
        "stage": "candidate",
    }

    with open(candidate_dir / "model.meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    promoted = False

    if promote:
        # 🟨 если current уже есть — архивируем
        if any(current_dir.iterdir()):
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            archived_version = archive_dir / ts
            archived_version.mkdir(parents=True)

            for file in current_dir.iterdir():
                (archived_version / file.name).write_bytes(file.read_bytes())

        # 🔹 promote candidate → current
        for file in candidate_dir.iterdir():
            (current_dir / file.name).write_bytes(file.read_bytes())

        promoted = True

    return {
        "status": "trained",
        "promoted": promoted,
        "models_dir": str(candidate_dir),
    }
