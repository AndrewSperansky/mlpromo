# app/ml_torch/data/dataset.py

import torch
from torch.utils.data import Dataset
import pandas as pd
import numpy as np
from typing import Optional, List, Tuple
from app.ml_torch.data.sequence_builder import SequenceBuilder


class UpliftTimeSeriesDataset(Dataset):
    """
    Датасет для обучения LSTM на временных рядах цен.

    Возвращает:
        - X: последовательность [seq_len, num_features]
        - y: целевое значение (k_uplift или цена)
    """

    def __init__(
            self,
            df: pd.DataFrame,
            feature_cols: List[str],
            target_col: str,
            seq_len: int = 30,
            transform: Optional[callable] = None
    ):
        """
        Args:
            df: DataFrame с данными (должен быть отсортирован по времени)
            feature_cols: колонки-признаки (price, sales, discount, ...)
            target_col: целевая колонка (k_uplift)
            seq_len: длина окна истории
            transform: трансформация признаков (нормализация)
        """
        self.df = df.reset_index(drop=True)
        self.feature_cols = feature_cols
        self.target_col = target_col
        self.seq_len = seq_len
        self.transform = transform

        self.builder = SequenceBuilder(seq_len=seq_len)

        # Предварительно строим все последовательности
        self.X, self.y = self._build_all_sequences()

    def _build_all_sequences(self) -> Tuple[np.ndarray, np.ndarray]:
        """Строит все окна из DataFrame"""
        if len(self.df) < self.seq_len + 1:
            raise ValueError(
                f"Недостаточно данных: нужно {self.seq_len + 1}, "
                f"получено {len(self.df)}"
            )

        # Преобразуем в числовой массив
        feature_values = self.df[self.feature_cols].values
        target_values = self.df[self.target_col].values

        X, y = [], []
        for i in range(len(self.df) - self.seq_len):
            X.append(feature_values[i:i + self.seq_len])
            y.append(target_values[i + self.seq_len])

        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        X = self.X[idx]
        y = self.y[idx]

        if self.transform:
            X = self.transform(X)

        return torch.tensor(X), torch.tensor(y)

    @classmethod
    def from_sku_history(
            cls,
            price_history: List[dict],
            feature_cols: List[str],
            target_col: str,
            seq_len: int = 30
    ):
        """
        Альтернативный конструктор: из истории цен (список словарей)

        price_history = [
            {"date": "2026-04-01", "price": 100, "k_uplift": 1.2},
            {"date": "2026-04-02", "price": 101, "k_uplift": 1.3},
            ...
        ]
        """
        df = pd.DataFrame(price_history)
        return cls(df, feature_cols, target_col, seq_len)