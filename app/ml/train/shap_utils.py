#  app/ml/train/shap_utils.py


import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from catboost import Pool

logger = logging.getLogger("promo_ml")


def compute_shap_catboost(
    model,
    X,
    categorical_features: List[str],
    validate: bool = True,
) -> Tuple[np.ndarray, float]:
    """
    Вычисляет SHAP values встроенным механизмом CatBoost.

    Parameters
    ----------
    model : CatBoostRegressor
        Обученная модель.
    X : pandas.DataFrame
        Данные с тем же набором признаков, что использовался при обучении.
    categorical_features : list[str]
        Список категориальных признаков.
    validate : bool
        Проверять ли корректность SHAP:
            prediction == expected_value + sum(shap_values)

    Returns
    -------
    shap_values : ndarray
        SHAP значения размерностью (n_samples, n_features)

    expected_value : float
        Базовое значение модели (base value)
    """

    # ==========================================================
    # 1. Проверяем совпадение порядка признаков
    # ==========================================================

    model_features = list(model.feature_names_)
    data_features = list(X.columns)

    if model_features != data_features:
        raise RuntimeError(
            "\nFeature order mismatch!\n\n"
            f"Model:\n{model_features}\n\n"
            f"Data:\n{data_features}"
        )

    # ==========================================================
    # 2. Проверяем категориальные признаки
    # ==========================================================

    missing = [
        feature
        for feature in categorical_features
        if feature not in X.columns
    ]

    if missing:
        raise ValueError(
            f"Categorical features not found: {missing}"
        )

    # ==========================================================
    # 3. Создаём Pool
    # ==========================================================

    pool = Pool(
        data=X,
        feature_names=model_features,
        cat_features=categorical_features,
    )

    # ==========================================================
    # 4. Вычисляем SHAP
    # ==========================================================

    shap_matrix = model.get_feature_importance(
        pool,
        type="ShapValues",
    )

    expected_columns = len(model_features) + 1

    if shap_matrix.shape[1] != expected_columns:
        raise ValueError(
            f"Unexpected SHAP shape {shap_matrix.shape}. "
            f"Expected second dimension = {expected_columns}"
        )

    expected_values = shap_matrix[:, -1]

    if not np.allclose(expected_values, expected_values[0]):
        logger.warning(
            "Expected value differs between rows "
            "(this is unusual)."
        )

    expected_value = float(np.mean(expected_values))

    shap_values = shap_matrix[:, :-1]

    # ==========================================================
    # 5. Проверяем корректность SHAP
    # ==========================================================

    if validate:

        prediction = model.predict(pool)

        reconstructed = (
            expected_value +
            np.sum(shap_values, axis=1)
        )

        if not np.allclose(
            prediction,
            reconstructed,
            atol=1e-6,
        ):

            max_error = np.max(
                np.abs(prediction - reconstructed)
            )

            raise RuntimeError(
                "SHAP validation failed.\n"
                f"Maximum reconstruction error = {max_error:.10f}"
            )

    logger.info(
        "SHAP successfully computed. "
        f"Samples={shap_values.shape[0]}, "
        f"Features={shap_values.shape[1]}, "
        f"ExpectedValue={expected_value:.6f}"
    )

    return shap_values, expected_value


def save_shap_artifacts(
    shap_values: np.ndarray,
    expected_value: float,
    feature_names: List[str],
    models_dir: Path,
    save_full_shap: bool = False,
) -> Dict[str, Any]:
    """
    Сохраняет SHAP артефакты.

    По умолчанию сохраняются только агрегированные показатели.

    Полный массив shap_values можно сохранить
    только при необходимости отладки.
    """

    models_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ==========================================================
    # Base Value
    # ==========================================================

    with open(models_dir / "shap_expected_value.json", "w", encoding="utf-8",) as f:
        json.dump({"expected_value": expected_value}, f, indent=2, ensure_ascii=False,)

    # ==========================================================
    # Средняя абсолютная важность
    # ==========================================================

    mean_abs = np.mean(np.abs(shap_values), axis=0,)

    # ==========================================================
    # Среднее направление влияния
    # ==========================================================

    mean_direction = np.mean(
        shap_values,
        axis=0,
    )

    summary = {}

    for feature, importance, direction in zip(
        feature_names,
        mean_abs,
        mean_direction,
    ):

        summary[feature] = {
            "importance": float(importance),
            "direction": float(direction),
        }

    summary = dict(
        sorted(
            summary.items(),
            key=lambda x: x[1]["importance"],
            reverse=True,
        )
    )

    with open(models_dir / "shap_summary.json",  "w", encoding="utf-8",) as f:
        json.dump(
            summary,
            f,
            indent=2,
            ensure_ascii=False,
        )

    # ==========================================================
    # Общая статистика
    # ==========================================================

    stats = {
        "expected_value": expected_value,
        "num_samples": int(shap_values.shape[0]),
        "num_features": int(shap_values.shape[1]),
        "min": float(np.min(shap_values)),
        "max": float(np.max(shap_values)),
        "mean": float(np.mean(shap_values)),
        "std": float(np.std(shap_values)),
        "top_features": list(summary.keys())[:10],
    }

    with open(models_dir / "shap_stats.json", "w", encoding="utf-8",) as f:
        json.dump(
            stats,
            f,
            indent=2,
            ensure_ascii=False,
        )

    # ==========================================================
    # Полный массив SHAP (опционально)
    # ==========================================================

    if save_full_shap:
        np.save(models_dir / "shap_values.npy",shap_values,)
        logger.warning("Full SHAP matrix saved: "f"{shap_values.shape}")
    else:
        logger.info("Only aggregated SHAP metrics saved.")

    logger.info("Top SHAP features: %s",", ".join(stats["top_features"]))

    return stats
