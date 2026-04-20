# app/ml/train/train_pipeline.py

import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

from catboost import CatBoostRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sqlalchemy.orm import Session

from app.ml.train.shap_utils import (
    compute_shap_catboost,
    save_shap_artifacts,
)

from app.ml.model_registry.lineage import enrich_meta_with_lineage
from app.ml.model_registry.promotion_policy import decide_promotion
from app.ml.model_registry.lineage import record_lineage_event

from app.services.registry_service import ModelRegistryService
from app.core.settings import settings
from app.db.session import SessionLocal
from app.ml.statistical_metrics import StatisticalMetrics
from app.ml.conformal import ConformalPredictor


logger = logging.getLogger("promo_ml")

TARGET = "k_uplift"


def ensure_dirs():

    current_dir = Path(settings.ML_CURRENT_DIR)  # /app/models/current
    candidate_dir = Path(settings.ML_CANDIDATE_DIR)  # /app/models/candidate
    metrics_dir = Path(settings.ML_METRICS_DIR)  # /app/models/metrics
    archive_dir = Path(settings.ML_ARCHIVE_DIR)

    current_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)


def load_full_dataset(db: Session) -> pd.DataFrame:
    """
    Загружает ВСЕ данные из industrial_dataset_raw
    """
    logger.info("📊 Loading full dataset from industrial_dataset_raw")

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


    candidate_dir = Path(settings.ML_CANDIDATE_DIR)
    current_dir = Path(settings.ML_CURRENT_DIR)
    archive_dir = Path(settings.ML_ARCHIVE_DIR)
    metrics_dir = Path(settings.ML_METRICS_DIR)

    candidate_dir.mkdir(parents=True, exist_ok=True)
    current_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)


    logger.info(f"📁 candidate_dir: {candidate_dir}")
    logger.info(f"📁 current_dir: {current_dir}")
    logger.info(f"📁 archive_dir: {archive_dir}")
    logger.info(f"📁 metrics_dir: {metrics_dir}")

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

    # ========== ОПРЕДЕЛЯЕМ ПРИЗНАКИ (FEATURES) ==========
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

    # ========== РАЗДЕЛЯЕМ ДАННЫЕ ==========

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    logger.info(f"📊 Train size: {len(X_train)}, Validation size: {len(X_val)}")

    # =========================
    # TRAIN
    # =========================
    # model = CatBoostRegressor(
    #     iterations=300,
    #     depth=6,
    #     learning_rate=0.05,
    #     loss_function="RMSE",
    #     random_seed=42,
    #     verbose=False,
    # )
    #
    # model.fit(X, y)
    #
    # preds = model.predict(X)
    # rmse_value = float(mean_squared_error(y, preds, squared=False))
    # logger.info(f"📈 Training RMSE: {rmse_value:.6f}")

    # =========================
    # TRAIN WITH VALIDATION
    # =========================

    model = CatBoostRegressor(
        iterations=500,  # увеличим до 500
        depth=6,
        learning_rate=0.05,
        loss_function="RMSE",
        random_seed=42,
        verbose=False,
        early_stopping_rounds=50  # остановка при отсутствии улучшений
    )

    # Обучаем с валидационной выборкой
    model.fit(
        X_train, y_train,
        eval_set=(X_val, y_val),
        verbose=False,
        plot=False
    )

    # Получаем метрики для графика
    evals_result = model.get_evals_result()
    train_rmse = evals_result['learn']['RMSE']
    val_rmse = evals_result['validation']['RMSE']
    iterations = list(range(1, len(train_rmse) + 1))

    # Сохраняем метрики в JSON для API
    training_metrics = {
        "iterations": iterations,
        "train_rmse": train_rmse,
        "val_rmse": val_rmse,
        "best_iteration": model.get_best_iteration(),
        "best_val_rmse": min(val_rmse)
    }

    # Сохраняем training_metrics.json в metrics/


    metrics_path = metrics_dir / "training_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(training_metrics, f, indent=2)

    # Для обратной совместимости — используем предсказания на ВСЕХ данных
    preds = model.predict(X)  # ← предсказания на всех данных
    rmse_value = float(mean_squared_error(y, preds, squared=False))
    logger.info(f"📈 Training RMSE (full dataset): {rmse_value:.6f}")

    # Для метрик модели используем validation RMSE (честная оценка)
    preds_val = model.predict(X_val)
    val_rmse_final = float(mean_squared_error(y_val, preds_val, squared=False))
    logger.info(f"📊 Validation RMSE (hold-out): {val_rmse_final:.6f}")


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
            metrics={"rmse": val_rmse_final},
            trained_rows_count=rows_used,
        )

        logger.info(f"✅ Model registered with id={db_model.id}")

        record_lineage_event(
            event_type="trained",
            model_id=str(db_model.id),
            reason=f"Training completed (trigger={trigger})",
            metadata={
                "rmse": val_rmse_final,
                "rows_used": rows_used
            }
        )

        logger.info(f"🔥🔥🔥 LINEAGE EVENT RECORDED: trained for model {db_model.id}")

        # =========================
        # СОХРАНЯЕМ МОДЕЛЬ
        # =========================
        model_filename = f"{db_model.id}.cbm"
        model_path = candidate_dir / model_filename
        model.save_model(str(model_path))

        # Обновляем путь в БД
        db_model.model_path = str(model_path)
        db.commit()
        db.refresh(db_model)  # ← обновляем объект из БД
        logger.info(f"✅ Model saved to {model_path}, DB path={db_model.model_path}")

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
        # META + LINEAGE (начальный)
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

        # ========== СТАТИСТИЧЕСКИЕ МЕТРИКИ (БЕЗ DATA LEAKAGE) ==========

        # Получаем текущую активную модель для сравнения
        db_local = SessionLocal()

        try:
            registry_local = ModelRegistryService(db_local)
            current_model = registry_local.get_active_model("promo_uplift")

            # Массив ошибок
            errors_array = np.array(y - preds)

            # 1. Confidence Interval для RMSE
            ci = StatisticalMetrics.calculate_confidence_interval(errors_array)

            # 2. Uplift (бизнес-метрика)
            uplift = StatisticalMetrics.calculate_uplift(y, preds)

            # 3. Accuracy с допуском
            accuracy_eps = StatisticalMetrics.accuracy_with_tolerance(y, preds, epsilon=5.0)

            # ========== CONFORMAL PREDICTION (С РАЗДЕЛЕНИЕМ НА CALIBRATION/TEST) ==========

            # Разделяем данные для калибровки и тестирования
            indices = np.random.permutation(len(y))
            calib_size = int(len(y) * 0.2)

            calib_indices = indices[:calib_size]
            test_indices = indices[calib_size:]

            # Преобразуем в numpy если нужно
            if hasattr(y, 'values'):
                y_array = y.values
                preds_array = preds if isinstance(preds, np.ndarray) else np.array(preds)
            else:
                y_array = np.array(y)
                preds_array = np.array(preds)

            y_calib = y_array[calib_indices]
            preds_calib = preds_array[calib_indices]

            y_test = y_array[test_indices]
            preds_test = preds_array[test_indices]

            # Калибровка на отдельной выборке
            cp = ConformalPredictor(alpha=0.05)
            cp.fit(y_calib, preds_calib)

            # Prediction interval для тестовых данных
            lower_test, upper_test = cp.predict(preds_test)

            # Coverage считаем ТОЛЬКО на тестовых данных
            coverage = cp.coverage(y_test, lower_test, upper_test)

            # 4. Статистическое сравнение с предыдущей моделью
            statistical_comparison = None
            if current_model and current_model.metrics:
                statistical_comparison = {
                    "note": "Requires previous model errors for paired t-test",
                    "test_used": "paired t-test (requires saved errors)",
                    "current_model_id": current_model.id,
                    "current_model_version": current_model.version
                }

            # Добавляем все метрики в meta
            meta["conformal_q_hat"] = cp.q_hat
            meta["conformal"] = cp.to_dict()
            meta["metrics"].update({
                "rmse": val_rmse_final,  # ← validation RMSE (честная оценка)

                # Дополнительные метрики для анализа
                "train_rmse": float(train_rmse[-1]),  # ← финальный train RMSE
                "val_rmse": val_rmse_final,  # ← дубль для ясности

                # Информация об обучении
                "best_iteration": model.get_best_iteration(),
                "total_iterations": len(train_rmse),

                # Статистические метрики
                "rmse_ci": ci,
                "uplift": uplift,
                "accuracy_eps": accuracy_eps,

                # Conformal prediction
                "coverage": coverage,
                "coverage_target": 0.95,
                "is_calibrated": abs(coverage - 0.95) <= 0.03,

                # Информация о выборках
                "sample_size": len(y),
                "train_size": len(X_train),
                "validation_size": len(X_val),
                "calibration_size": calib_size,
                "test_size": len(y_test),
            })

            if statistical_comparison:
                meta["metrics"]["statistical_comparison"] = statistical_comparison

            logger.info(
                f"📊 Statistical metrics added: RMSE_CI={ci['rmse']:.6f}, coverage={coverage:.3f}, uplift={uplift:.4f}")

        finally:
            db_local.close()

        # ===== СОХРАНЯЕМ META В ФАЙЛ (ПОСЛЕ ДОБАВЛЕНИЯ ВСЕХ МЕТРИК) =====
        meta_path = candidate_dir / f"{db_model.id}.meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"✅ Meta saved to {meta_path} with conformal_q_hat={cp.q_hat}")

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

    # ========== ВЫЧИСЛЯЕМ COMPARISON ДЛЯ UI ВСЕГДА !!!! ==========

    # if promote is False:   <--  Удалили

    comparison = None
    db_local = SessionLocal()
    try:
        registry_local = ModelRegistryService(db_local)
        current_model = registry_local.get_active_model("promo_uplift")

        current_metrics_dict = None
        if current_model and current_model.metrics is not None:
            if isinstance(current_model.metrics, dict):
                current_metrics_dict = current_model.metrics
            else:
                current_metrics_dict = json.loads(current_model.metrics) if isinstance(current_model.metrics,
                                                                                       str) else None

        new_metrics_dict = meta.get("metrics") if isinstance(meta.get("metrics"), dict) else None

        if current_model and current_metrics_dict and new_metrics_dict:
            current_rmse = current_metrics_dict.get("rmse")
            new_rmse = new_metrics_dict.get("rmse")

            if current_rmse is not None and new_rmse is not None:
                is_better = new_rmse < current_rmse
                rmse_delta = current_rmse - new_rmse
                improvement_percent = (rmse_delta / current_rmse) * 100 if current_rmse != 0 else 0

                metrics_diff = {}
                all_metrics = set(current_metrics_dict.keys()) | set(new_metrics_dict.keys())

                for metric in all_metrics:
                    curr = current_metrics_dict.get(metric)
                    new = new_metrics_dict.get(metric)

                    if curr is not None and new is not None:
                        if metric in ["rmse", "mae", "mape"]:
                            metrics_diff[metric] = round(curr - new, 6)
                        else:
                            metrics_diff[metric] = round(new - curr, 6)

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

    # 🔥 Логируем что возвращаем
    logger.info(f"📦 Returning comparison: {json.dumps(comparison, indent=2) if comparison else 'None'}")
    logger.info(f"🔍 Returning comparison: {comparison}")
    logger.info(f"🔍 FINAL comparison type: {type(comparison)}")

    return {
        "status": "trained",
        "model_id": db_model.id,
        "metrics": meta["metrics"],
        "promoted": promoted,
        "stage": meta.get("stage", "candidate"),
        "comparison": comparison,
        "promotion_decision": promotion_decision,
        "rows_original": original_count,
        "rows_used": rows_used,
        "rows_removed": original_count - rows_used,
        "model_name": "promo_uplift",
    }