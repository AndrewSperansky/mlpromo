# app/ml_torch/data/dataset.py

import logging
import torch
from torch.utils.data import Dataset
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger("promo_ml")

class UpliftTimeSeriesDataset(Dataset):
    """
    Датасет для LSTM с поддержкой:
    - числовых фич
    - категориальных фич (через эмбеддинги)
    """

    def __init__(
            self,
            df: pd.DataFrame,
            numeric_features: List[str],
            categorical_features: List[str],
            target_col: str,
            seq_len: int = 30,
    ):
        """
        Args:
            df: DataFrame с данными (отсортирован по дате)
            numeric_features: список числовых колонок
            categorical_features: список категориальных колонок
            target_col: целевая колонка
            seq_len: длина окна истории
        """
        self.df = df.reset_index(drop=True)
        self.numeric_features = numeric_features
        self.categorical_features = categorical_features
        self.target_col = target_col
        self.seq_len = seq_len

        # Кодируем категориальные признаки
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self._encode_categorical()

        # Строим последовательности
        self.X_numeric, self.X_categorical, self.y = self._build_sequences()

    def _encode_categorical(self):
        """Превращает категории в числа (для эмбеддингов)"""
        for col in self.categorical_features:
            le = LabelEncoder()
            # -1 для неизвестных значений (защита)
            self.df[col] = self.df[col].astype(str)
            self.df[f"{col}_encoded"] = le.fit_transform(self.df[col])
            self.label_encoders[col] = le
            logger.info(f"Encoded {col}: {len(le.classes_)} unique values")

    def _build_sequences(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Строит окна для LSTM"""
        if len(self.df) < self.seq_len + 1:
            raise ValueError(
                f"Need at least {self.seq_len + 1} rows, got {len(self.df)}"
            )

        # Числовые данные
        numeric_data = self.df[self.numeric_features].values

        # Категориальные данные (закодированные)
        cat_cols = [f"{col}_encoded" for col in self.categorical_features]
        categorical_data = self.df[cat_cols].values

        # Целевая переменная (next_day_price или next_week_quantity)
        target_data = self.df[self.target_col].values

        X_num, X_cat, y = [], [], []

        for i in range(len(self.df) - self.seq_len):
            X_num.append(numeric_data[i:i + self.seq_len])
            X_cat.append(categorical_data[i:i + self.seq_len])
            y.append(target_data[i + self.seq_len])

        return (
            np.array(X_num, dtype=np.float32),
            np.array(X_cat, dtype=np.int64),
            np.array(y, dtype=np.float32)
        )

    def __len__(self):
        return len(self.X_numeric)

    def __getitem__(self, idx):
        return (
            torch.tensor(self.X_numeric[idx]),
            torch.tensor(self.X_categorical[idx]),
            torch.tensor(self.y[idx])
        )

    def get_embedding_dims(self) -> Dict[str, int]:
        """Возвращает размеры эмбеддингов для каждого категориального признака"""
        return {
            col: len(le.classes_)
            for col, le in self.label_encoders.items()
        }

    def get_label_encoders_serializable(self) -> Dict[str, List[str]]:
        """Возвращает классы энкодеров для сохранения"""
        return {
            name: list(le.classes_)
            for name, le in self.label_encoders.items()
        }