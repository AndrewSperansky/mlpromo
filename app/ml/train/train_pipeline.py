# app/ml/train/train_pipeline.py

import json
import logging
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
from app.services.registry_service import ModelRegistryService
from app.core.settings import settings
from app.db.session import SessionLocal


logger = logging.getLogger(__name__)


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

    # ========== ВАЖНО: УДАЛЯЕМ СТРОКИ С NULL В ЦЕЛЕВОЙ ПЕРЕМЕННОЙ ==========
    original_count = len(df)
    df = df.dropna(subset=[TARGET])
    cleaned_count = len(df)

    if cleaned_count == 0:
        raise ValueError(f"All {original_count} rows have NULL target values! Cannot train.")

    if cleaned_count < original_count:
        logger.warning(f"Removed {original_count - cleaned_count} rows with NULL target values")

    rows_used = cleaned_count
    # ======================================================================

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

    # =========================
    # REGISTRATION (ПОЛУЧАЕМ ID)
    # =========================
    db = SessionLocal()
    try:
        registry = ModelRegistryService(db)

        # Сначала регистрируем модель (без model_path)
        db_model = registry.register_model(
            name="promo_uplift",
            version=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S'),  # читаемая версия
            algorithm="catboost",
            model_type="regression",
            target=TARGET,
            features=FEATURES,
            metrics={"rmse": rmse_value},
            dataset_version_id=dataset_version_id,
            trained_rows_count=rows_used,
        )

        # =========================
        # СОХРАНЯЕМ МОДЕЛЬ С ИМЕНЕМ = ID
        # =========================
        model_filename = f"{db_model.id}.cbm"
        model_path = candidate_dir / model_filename
        model.save_model(str(model_path))

        # Обновляем путь в БД
        db_model.model_path = str(model_path)
        db.commit()

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
            "model_id": db_model.id,
            "model_name": "promo_uplift",
            "dataset_version_id": str(dataset_version_id),
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "features": FEATURES,
            "stage": "candidate",
            "metrics": {
                "rmse": rmse_value,
            },
        }

        meta = enrich_meta_with_lineage(meta=meta, trigger=trigger)

        meta_path = candidate_dir / f"{db_model.id}.meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        promoted = False
        promotion_decision = None

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

    logger.info(f"🔥 TRAIN PIPELINE RESULT: model_id={db_model.id} (type={type(db_model.id)})")
    result_dict = {
        'status': 'trained',
        'model_id': db_model.id,
        'metrics': meta['metrics'],
        'promoted': promoted,
        'stage': meta['stage'],
        'promotion_decision': promotion_decision,
        'rows_original': original_count,
        'rows_used': rows_used,
        'rows_removed': original_count - rows_used,
        'model_name': 'promo_uplift'
    }
    logger.info(f"🔥 TRAIN PIPELINE RESULT: {result_dict}")

    return {
        "status": "trained",
        "model_id": db_model.id,
        "metrics": meta["metrics"],
        "promoted": promoted,
        "stage": meta["stage"],
        "promotion_decision": promotion_decision,
        "rows_original": original_count,
        "rows_used": rows_used,
        "rows_removed": original_count - rows_used,
        "model_name": "promo_uplift",
    }