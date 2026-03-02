# app/ml/train/train_pipeline.py

import json
import pandas as pd
from uuid import UUID
from pathlib import Path
from datetime import datetime, timezone

from catboost import CatBoostRegressor
from sklearn.metrics import mean_squared_error
from sqlalchemy.orm import Session
from sqlalchemy import text


from app.ml.train.shap_utils import (
    compute_shap_catboost,
    save_shap_artifacts,
)

from app.ml.model_registry.lineage import enrich_meta_with_lineage
from app.ml.model_registry.promotion_policy import decide_promotion
from app.ml.registry.service import ModelRegistryService
from app.core.settings import settings
from app.db.session import SessionLocal


TARGET = "SalesQty_Promo"


def _get_models_dir() -> Path:
    return Path(settings.ML_MODEL_DIR)


def load_dataset_by_version(
        db: Session,
        dataset_version_id: UUID
) -> pd.DataFrame:


    # 🔧 ИСПРАВЛЕНО: используем text() для безопасного запроса
    query = text("""
        SELECT * FROM industrial_dataset_raw 
        WHERE dataset_version_id = :version_id
    """)

    df = pd.read_sql(
        query,
        db.bind,
        params={"version_id": dataset_version_id}
    )

    return df


def train_pipeline(
    dataset_version_id: UUID,
    promote: bool = False,
    trigger: str = "manual",
) -> dict:

    MODELS_DIR = _get_models_dir()

    candidate_dir = MODELS_DIR / "_candidate"
    current_dir = MODELS_DIR / "current"
    archive_dir = MODELS_DIR / "archive"

    candidate_dir.mkdir(parents=True, exist_ok=True)
    current_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    # =========================
    # LOAD DATASET
    # =========================

    db: Session = SessionLocal()
    try:
        df = load_dataset_by_version(db, dataset_version_id)
    finally:
        db.close()

    if df.empty:
        raise RuntimeError("Dataset is empty.")

    rows_used = len(df)

    # 🔧 ИСПРАВЛЕНО: самый простой способ - напрямую использовать columns
    exclude_cols = {"id", "dataset_version_id", TARGET}

    # Получаем все числовые колонки
    numeric_columns = []
    for col in df.columns:
        if col in exclude_cols:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_columns.append(col)

    FEATURES = numeric_columns

    X = df[FEATURES]
    y = df[TARGET]

    # =========================
    # TRAIN
    # =========================

    model = CatBoostRegressor(
        iterations=300,
        depth=6,
        learning_rate=0.05,
        loss_function="RMSE",
        random_seed=42,
        verbose=False,
    )

    model.fit(X, y)

    preds = model.predict(X)
    rmse_value = float(mean_squared_error(y, preds, squared=False))

    model_id = datetime.now(timezone.utc).isoformat()

    model_path = candidate_dir / f"{model_id}.cbm"
    model.save_model(str(model_path))

    # =========================
    # SHAP
    # =========================

    shap_values, expected_value = compute_shap_catboost(
        model=model,
        X=X,
    )

    save_shap_artifacts(
        shap_values=shap_values,
        expected_value=expected_value,
        feature_names=FEATURES,
        models_dir=candidate_dir,
    )

    # =========================
    # META + LINEAGE
    # =========================

    meta = {
        "model_id": model_id,
        "model_name": "promo_uplift",
        "dataset_version_id": str(dataset_version_id),
        "trained_at": model_id,
        "features": FEATURES,
        "stage": "candidate",
        "metrics": {
            "rmse": rmse_value,
        },
    }

    meta = enrich_meta_with_lineage(meta=meta, trigger=trigger)

    meta_path = candidate_dir / f"{model_id}.meta.json"

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    promoted = False
    promotion_decision = None

    # =========================
    # REGISTRATION-METRICS-GATED PROMOTION
    # =========================

    db = SessionLocal()
    try:
        registry = ModelRegistryService(db)

        db_model = registry.register_model(
            name="promo_uplift",
            version=model_id,
            algorithm="catboost",
            model_type="regression",
            target=TARGET,
            features=FEATURES,
            metrics=meta["metrics"],
            model_path=model_path,
            dataset_version_id=dataset_version_id,
            trained_rows_count=rows_used,
        )

        if promote:
            current_active_model = registry.get_active_model("promo_uplift")

            current_metrics = (
                current_active_model.metrics if current_active_model else None
            )

            promotion_decision = decide_promotion(
                candidate_metrics=meta["metrics"],
                current_metrics=current_metrics,
            )

            if promotion_decision["promote"]:
                registry.promote_model(db_model.id)
                promoted = True
                meta["stage"] = "current"

    finally:
        db.close()

    return {
        "status": "trained",
        "model_id": model_id,
        "metrics": meta["metrics"],
        "promoted": promoted,
        "stage": meta["stage"],
        "promotion_decision": promotion_decision,
    }

