# app/ml/train/train_pipeline.py

import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

from catboost import CatBoostRegressor
from sklearn.metrics import mean_squared_error
from sqlalchemy.orm import Session

from app.ml.train.shap_utils import (
    compute_shap_catboost,
    save_shap_artifacts,
)
from app.ml.model_registry.lineage import enrich_meta_with_lineage
from app.ml.model_registry.promotion_policy import decide_promotion
from app.services.registry_service import ModelRegistryService
from app.core.settings import settings
from app.db.session import SessionLocal
from models.industrial_dataset import IndustrialDatasetRaw

logger = logging.getLogger(__name__)

TARGET = "k_uplift"


def _get_models_dir() -> Path:
    return Path(settings.ML_MODEL_DIR)


def load_full_dataset(db: Session) -> pd.DataFrame:
    """
    Загружает ВСЕ данные из industrial_dataset_raw
    """
    logger.info("📊 Loading full dataset from industrial_dataset_raw")

    # Используем SQL запрос для загрузки всех данных
    from sqlalchemy import text

    query = text("""
        SELECT 
            promo_id,
            sku,
            store_id,
            category,
            region,
            store_location_type,
            format_assortment,
            month,
            week,
            regular_price,
            promo_price,
            promo_mechanics,
            adv_carrier,
            adv_material,
            marketing_type,
            analog_sku,
            k_uplift,
            extra_features
        FROM industrial_dataset_raw
        WHERE k_uplift IS NOT NULL
    """)

    df = pd.read_sql(query, db.bind)

    if df.empty:
        raise ValueError("No data in industrial_dataset_raw")

    logger.info(f"✅ Loaded {len(df)} rows from dataset")
    logger.info(f"📋 Columns: {list(df.columns)}")

    return df


def train_pipeline(
        promote: bool = False,
        trigger: str = "manual",
) -> dict:
    """
    Обучает модель на ВСЁМ датасете из industrial_dataset_raw
    """
    logger.info(f"🚀 Starting training pipeline (promote={promote}, trigger={trigger})")

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
        df = load_full_dataset(db)
    finally:
        db.close()

    if df.empty:
        raise RuntimeError("Dataset is empty.")

    # ========== УДАЛЯЕМ СТРОКИ С NULL В ЦЕЛЕВОЙ ПЕРЕМЕННОЙ ==========
    original_count = len(df)
    df = df.dropna(subset=[TARGET])
    cleaned_count = len(df)

    if cleaned_count == 0:
        raise ValueError(f"All {original_count} rows have NULL target values! Cannot train.")

    if cleaned_count < original_count:
        logger.warning(f"Removed {original_count - cleaned_count} rows with NULL target values")

    rows_used = cleaned_count

    # ========== ОПРЕДЕЛЯЕМ ПРИЗНАКИ ==========
    exclude_cols = {"id", TARGET}

    numeric_columns = []
    for col in df.columns:
        if col in exclude_cols:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_columns.append(col)

    FEATURES = numeric_columns

    X = df[FEATURES]
    y = df[TARGET]

    logger.info(f"📊 Features ({len(FEATURES)}): {FEATURES}")

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
    logger.info(f"📈 Training RMSE: {rmse_value:.6f}")

    # =========================
    # REGISTRATION
    # =========================
    db = SessionLocal()
    try:
        registry = ModelRegistryService(db)

        # Регистрируем модель
        db_model = registry.register_model(
            name="promo_uplift",
            version=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S'),
            algorithm="catboost",
            model_type="regression",
            target=TARGET,
            features=FEATURES,
            metrics={"rmse": rmse_value},
            trained_rows_count=rows_used,
        )

        logger.info(f"✅ Model registered with id={db_model.id}")

        # =========================
        # СОХРАНЯЕМ МОДЕЛЬ
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
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "features": FEATURES,
            "stage": "candidate",
            "metrics": {
                "rmse": rmse_value,
            },
            "total_rows": rows_used,
        }

        meta = enrich_meta_with_lineage(meta=meta, trigger=trigger)

        meta_path = candidate_dir / f"{db_model.id}.meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        # =========================
        # PROMOTION
        # =========================
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
                logger.info(f"🎉 Model {db_model.id} promoted to champion")
            else:
                logger.warning(f"Promotion rejected by policy: {promotion_decision['reason']}")

    finally:
        db.close()

    logger.info(f"✅ Training pipeline completed: model_id={db_model.id}, promoted={promoted}")

    # ========== ВЫЧИСЛЯЕМ COMPARISON ДЛЯ UI ==========
    comparison = None
    if promote is False:  # Для ручной активации
        db_local = SessionLocal()
        try:
            registry_local = ModelRegistryService(db_local)
            current_model = registry_local.get_active_model("promo_uplift")

            # 🔥 КЛЮЧ: Преобразуем Mapped в обычный dict
            current_metrics_dict = None
            if current_model and current_model.metrics is not None:
                # metrics может быть уже dict или нужно преобразовать
                if isinstance(current_model.metrics, dict):
                    current_metrics_dict = current_model.metrics
                else:

                    current_metrics_dict = json.loads(current_model.metrics) if isinstance(current_model.metrics, str) else None

            new_metrics_dict = meta.get("metrics") if isinstance(meta.get("metrics"), dict) else None

            if current_model and current_metrics_dict and new_metrics_dict:
                current_rmse = current_metrics_dict.get("rmse")
                new_rmse = new_metrics_dict.get("rmse")

                if current_rmse is not None and new_rmse is not None:
                    is_better = new_rmse < current_rmse
                    rmse_delta = current_rmse - new_rmse
                    improvement_percent = (rmse_delta / current_rmse) * 100 if current_rmse != 0 else 0

                    # Формируем diff для таблицы
                    metrics_diff = {}
                    all_metrics = set(current_metrics_dict.keys()) | set(new_metrics_dict.keys())

                    for metric in all_metrics:
                        curr = current_metrics_dict.get(metric)
                        new = new_metrics_dict.get(metric)

                        if curr is not None and new is not None:
                            # lower_is_better: rmse, mae, mape
                            if metric in ["rmse", "mae", "mape"]:
                                metrics_diff[metric] = round(curr - new, 6)  # положительный = улучшение
                            else:  # r2, accuracy, etc.
                                metrics_diff[metric] = round(new - curr, 6)  # положительный = улучшение

                    comparison = {
                        "current_model_id": current_model.id,
                        "candidate_model_id": db_model.id,
                        "current_metrics": current_metrics_dict,
                        "candidate_metrics": new_metrics_dict,
                        "is_better": is_better,
                        "rmse_delta": round(rmse_delta, 6),
                        "improvement_percent": round(improvement_percent, 2),
                        "metrics_diff": metrics_diff,
                    }

                    logger.info(f"📊 Comparison computed: is_better={is_better}, improvement={improvement_percent:.2f}%")
                else:
                    logger.warning(f"Missing RMSE: current={current_rmse}, new={new_rmse}")
            else:
                logger.info("No current model or metrics, skipping comparison")
        except Exception as e:
            logger.error(f"Failed to compute comparison: {e}", exc_info=True)
        finally:
            db_local.close()

    return {
        "status": "trained",
        "model_id": db_model.id,
        "metrics": meta["metrics"],
        "promoted": promoted,
        "stage": meta["stage"],
        "comparison": comparison,
        "promotion_decision": promotion_decision,
        "rows_original": original_count,
        "rows_used": rows_used,
        "rows_removed": original_count - rows_used,
        "model_name": "promo_uplift",
    }