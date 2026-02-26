# app/ml/train/train_pipeline.py
# — TRAIN PIPELINE WITH VERSIONING + ARCHIVE CONTRACT + LINEAGE + PROMOTION POLICY

from pathlib import Path
from datetime import datetime, timezone
import json
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.metrics import mean_squared_error

from app.ml.train.shap_utils import (
    compute_shap_catboost,
    save_shap_artifacts,
)

from app.ml.model_registry.lineage import enrich_meta_with_lineage
from app.ml.model_registry.promotion_policy import decide_promotion
from app.core.settings import settings
from app.api.v1.ml.dataset import load_dataset


# ==========================================================
# CONFIG
# ==========================================================

FEATURES = [
    "price",
    "discount",
    "avg_sales_7d",
    "promo_days_left",
]

TARGET = "target_sales_qty"


# ==========================================================
# MODELS DIR
# ==========================================================

def _get_models_dir() -> Path:
    """
    MODELS_DIR читается в момент вызова
    """
    return Path(settings.ML_MODEL_DIR)


# ==========================================================
# DATA PREPARATION
# ==========================================================

def _prepare_training_data_synthetic():
    """
    Используется ТОЛЬКО в test окружении
    """
    data = pd.DataFrame(
        {
            "price": [100, 120, 90, 110],
            "discount": [10, 20, 0, 15],
            "avg_sales_7d": [30, 25, 40, 28],
            "promo_days_left": [5, 3, 10, 2],
            "target_sales_qty": [140, 160, 135, 150],
        }
    )

    X = data[FEATURES]
    y = data[TARGET]

    # train == val (для smoke)
    return X, y, X, y


def _prepare_training_data_time_split(val_days: int = 4):
    """
    Production training.
    Time-based split для предотвращения data leakage.
    """
    df = load_dataset(limit=50_000)

    if df.empty:
        raise RuntimeError("Dataset is empty. Training aborted.")

    df["date"] = pd.to_datetime(df["date"])
    max_date = df["date"].max()
    split_date = max_date - pd.Timedelta(days=val_days)

    train_df = df[df["date"] <= split_date]
    val_df = df[df["date"] > split_date]

    if train_df.empty or val_df.empty:
        raise RuntimeError("Train/validation split failed. Not enough data.")

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]

    X_val = val_df[FEATURES]
    y_val = val_df[TARGET]

    return X_train, y_train, X_val, y_val


# ==========================================================
# TRAIN PIPELINE
# ==========================================================

def train_pipeline(
    promote: bool = False,
    trigger: str = "manual",
) -> dict:
    """
    promote=False → candidate only
    promote=True  → candidate → metrics-gated promotion → current + archive
    """

    MODELS_DIR = _get_models_dir()

    candidate_dir = MODELS_DIR / "_candidate"
    current_dir = MODELS_DIR / "current"
    archive_dir = MODELS_DIR / "archive"

    # =========================
    # 0️⃣ INFRASTRUCTURE
    # =========================
    candidate_dir.mkdir(parents=True, exist_ok=True)
    current_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    # =========================
    # 1️⃣ DATA SELECTION
    # =========================

    if settings.ENVIRONMENT == "test":
        X_train, y_train, X_val, y_val = _prepare_training_data_synthetic()
    else:
        X_train, y_train, X_val, y_val = _prepare_training_data_time_split()

    feature_names = FEATURES

    # =========================
    # 2️⃣ TRAIN MODEL
    # =========================

    model = CatBoostRegressor(
        iterations=300,
        depth=6,
        learning_rate=0.05,
        loss_function="RMSE",
        random_seed=42,
        verbose=False,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=(X_val, y_val),
        use_best_model=True,
    )

    preds = model.predict(X_val)
    rmse_value = float(mean_squared_error(y_val, preds, squared=False))

    model_path = candidate_dir / "cb_promo_v1.cbm"
    model.save_model(str(model_path), format="cbm")

    # =========================
    # 3️⃣ SHAP ARTIFACTS
    # =========================

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

    # =========================
    # 4️⃣ METADATA + LINEAGE
    # =========================

    model_id = datetime.now(timezone.utc).isoformat()

    meta = {
        "model_id": model_id,
        "model_name": "promo_uplift",
        "trained_at": model_id,
        "features": feature_names,
        "artifacts": {
            "model": "cb_promo_v1.cbm",
            "shap_summary": "shap_summary.json",
        },
        "stage": "candidate",
        "metrics": {
            "rmse": rmse_value,
        },
    }

    meta = enrich_meta_with_lineage(
        meta=meta,
        trigger=trigger,
    )

    meta_path = candidate_dir / "cb_promo_v1.meta.json"

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    promoted = False
    promotion_decision = None

    # =========================
    # 5️⃣ METRICS-GATED PROMOTION
    # =========================

    if promote:
        current_metrics = None

        current_meta_path = current_dir / "cb_promo_v1.meta.json"

        if current_meta_path.exists():
            with open(current_meta_path) as f:
                current_meta = json.load(f)
                current_metrics = current_meta.get("metrics")

        promotion_decision = decide_promotion(
            candidate_metrics=meta["metrics"],
            current_metrics=current_metrics,
        )

        meta["promotion_decision"] = promotion_decision

        if promotion_decision["promote"]:
            # 🟨 archive current
            if any(current_dir.iterdir()):
                ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                archived_version = archive_dir / ts
                archived_version.mkdir(parents=True)

                for file in current_dir.iterdir():
                    (archived_version / file.name).write_bytes(
                        file.read_bytes()
                    )

            # 🔹 promote candidate → current
            for file in candidate_dir.iterdir():
                (current_dir / file.name).write_bytes(
                    file.read_bytes()
                )

            promoted = True
            meta["stage"] = "current"

        # audit update
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

    # =========================
    # 6️⃣ RESPONSE
    # =========================

    return {
        "status": "trained",
        "model_id": model_id,
        "metrics": meta["metrics"],
        "promoted": promoted,
        "stage": meta["stage"],
        "promotion_decision": promotion_decision,
    }