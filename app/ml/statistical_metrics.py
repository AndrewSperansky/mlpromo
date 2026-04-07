# app/ml/statistical_metrics.py

import numpy as np
from scipy import stats
from typing import Dict, Any, Tuple, Optional


class StatisticalMetrics:
    """
    Статистические метрики для оценки и сравнения моделей
    """

    @staticmethod
    def calculate_confidence_interval(
            errors: np.ndarray,
            confidence: float = 0.95
    ) -> Dict[str, float]:
        """
        CI (Confidence Interval — доверительный интервал) для RMSE

        Args:
            errors: массив ошибок (y_true - y_pred)
            confidence: уровень доверия (0.95 = 95%)

        Returns:
            dict с rmse, lower, upper
        """
        # Исправлено: считаем RMSE, а не среднюю ошибку
        squared_errors = errors ** 2
        rmse = np.sqrt(np.mean(squared_errors))

        std = np.std(squared_errors)
        n = len(squared_errors)

        z = stats.norm.ppf((1 + confidence) / 2)
        margin = z * (std / np.sqrt(n))

        return {
            "rmse": float(rmse),
            "lower": float(max(0, rmse - margin)),  # RMSE не может быть отрицательным
            "upper": float(rmse + margin),
            "confidence_level": confidence,
            "margin": float(margin)
        }

    @staticmethod
    def calculate_prediction_interval(
            preds: np.ndarray,
            errors: np.ndarray,
            confidence: float = 0.95
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Расчет prediction interval для прогнозов
        """
        std = float(np.std(errors))
        z = stats.norm.ppf((1 + confidence) / 2)

        lower = preds - z * std
        upper = preds + z * std

        return lower, upper

    @staticmethod
    def calculate_coverage(
            y_true: np.ndarray,
            lower: np.ndarray,
            upper: np.ndarray
    ) -> float:
        """
        Расчет coverage — вероятности попадания в интервал
        """
        return float(((y_true >= lower) & (y_true <= upper)).mean())

    @staticmethod
    def accuracy_with_tolerance(
            y_true: np.ndarray,
            y_pred: np.ndarray,
            epsilon: float = 5.0
    ) -> float:
        """
        Accuracy с допуском — процент предсказаний в пределах epsilon
        """
        return float(np.mean(np.abs(y_true - y_pred) < epsilon))

    @staticmethod
    def calculate_uplift(
            y_true: np.ndarray,
            y_pred: np.ndarray
    ) -> float:
        """
        Бизнес-метрика — средний абсолютный прирост

        TODO: Заменить на реальный бизнес KPI (revenue, margin, etc.)
        """
        return float(np.mean(np.abs(y_pred - y_true)))

    @staticmethod
    def compare_models_statistically(
            errors_new: np.ndarray,
            errors_old: np.ndarray
    ) -> Dict[str, Any]:
        """
        Статистическое сравнение двух моделей (зависимые выборки)

        Args:
            errors_new: ошибки новой модели
            errors_old: ошибки старой модели (на тех же данных)

        Returns:
            dict с t-statistic, p-value, is_significant
        """
        # Исправлено: используем ttest_rel для зависимых выборок
        t_stat, p_value = stats.ttest_rel(errors_old, errors_new)

        return {
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "is_significant": p_value < 0.05,
            "interpretation": "Statistically significant" if p_value < 0.05 else "Not significant",
            "test_used": "paired t-test"
        }