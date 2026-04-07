# app/ml/conformal.py

import numpy as np
from typing import Tuple, Dict, Any


class ConformalPredictor:
    """
    Conformal Prediction — гарантированное coverage без предположений о распределении

    Исправлено: добавлена поправка для гарантированного coverage
    """

    def __init__(self, alpha: float = 0.05):
        """
        Args:
            alpha: уровень ошибки (0.05 = 95% интервал)
        """
        self.alpha = alpha
        self.q_hat = None
        self.calibration_size = None

    def fit(self, y_true: np.ndarray, y_pred: np.ndarray) -> None:
        """
        Калибровка на hold-out выборке

        Args:
            y_true: истинные значения
            y_pred: предсказания
        """
        # Nonconformity scores — абсолютные ошибки
        errors = np.abs(y_true - y_pred)
        n = len(errors)

        # Исправлено: поправка для гарантированного coverage
        # q = ceil((n+1)*(1-alpha)) / n
        q = np.ceil((n + 1) * (1 - self.alpha)) / n
        self.q_hat = np.quantile(errors, q, method='higher')
        self.calibration_size = n

    def predict(self, preds: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Возвращает prediction interval

        Args:
            preds: предсказания модели

        Returns:
            lower, upper bounds
        """
        if self.q_hat is None:
            raise ValueError("Model not calibrated. Call fit() first.")

        lower = preds - self.q_hat
        upper = preds + self.q_hat

        return lower, upper

    def coverage(self, y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
        """
        Расчет coverage на тестовых данных
        """
        return float(((y_true >= lower) & (y_true <= upper)).mean())

    def get_interval_width(self) -> float:
        """Средняя ширина интервала"""
        if self.q_hat is None:
            return 0.0
        return float(2 * self.q_hat)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация для сохранения в метаданные"""
        return {
            "alpha": self.alpha,
            "q_hat": float(self.q_hat) if self.q_hat is not None else None,
            "calibration_size": self.calibration_size,
            "interval_width": self.get_interval_width()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConformalPredictor":
        """Десериализация из метаданных"""
        predictor = cls(alpha=data.get("alpha", 0.05))
        predictor.q_hat = data.get("q_hat")
        predictor.calibration_size = data.get("calibration_size")
        return predictor