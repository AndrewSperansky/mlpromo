# app/ml_torch/data/sequence_builder.py

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta


class SequenceBuilder:
    """
    Строит последовательности (окна) для обучения LSTM.

    Принцип: скользящее окно длиной `seq_len` скользит по временному ряду.
    Для каждого окна: features = окно истории, target = следующее значение.

    Пример для seq_len = 3:
        [day1, day2, day3] -> day4
        [day2, day3, day4] -> day5
        [day3, day4, day5] -> day6
    """

    def __init__(self, seq_len: int = 30):
        """
        Args:
            seq_len: длина окна (сколько дней истории подаём на вход)
        """
        self.seq_len = seq_len

    def build_sequence(
            self,
            values: List[float],
            target_col: str = "price"
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Преобразует временной ряд в последовательности (X, y)

        Args:
            values: список значений (цены, продажи)
            target_col: название для логирования

        Returns:
            X: массив окон [num_windows, seq_len]
            y: массив таргетов [num_windows]
        """
        if len(values) < self.seq_len + 1:
            raise ValueError(
                f"Недостаточно данных: нужно {self.seq_len + 1}, получено {len(values)}"
            )

        X, y = [], []
        for i in range(len(values) - self.seq_len):
            X.append(values[i:i + self.seq_len])
            y.append(values[i + self.seq_len])

        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    def build_multi_feature_sequence(
            self,
            df: pd.DataFrame,
            feature_cols: List[str],
            target_col: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Строит последовательности из нескольких временных рядов

        Args:
            df: DataFrame с колонками date, feature_cols, target_col
            feature_cols: список признаков (price, sales, ...)
            target_col: целевая переменная

        Returns:
            X: [num_windows, seq_len, num_features]
            y: [num_windows]
        """
        if len(df) < self.seq_len + 1:
            raise ValueError(
                f"Недостаточно данных: нужно {self.seq_len + 1}, получено {len(df)}"
            )

        # Сортируем по дате
        df = df.sort_values('date')

        # Берём числовые значения
        feature_values = df[feature_cols].values
        target_values = df[target_col].values

        X, y = [], []
        for i in range(len(df) - self.seq_len):
            X.append(feature_values[i:i + self.seq_len])
            y.append(target_values[i + self.seq_len])

        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    def pad_sequence(
            self,
            values: List[float],
            padding_value: float = 0.0
    ) -> np.ndarray:
        """
        Дополняет последовательность до нужной длины (если данных меньше seq_len)

        Args:
            values: список значений
            padding_value: чем дополнять (обычно 0)
        """
        if len(values) >= self.seq_len:
            return np.array(values[-self.seq_len:], dtype=np.float32)

        # Не хватает данных — дополняем слева
        pad_size = self.seq_len - len(values)
        padded = [padding_value] * pad_size + values
        return np.array(padded, dtype=np.float32)