# app/ml_torch/models/lstm.py

import torch
import torch.nn as nn
from typing import Optional, List, Dict
from .base import BaseTorchModel


class LSTMUpliftModel(BaseTorchModel):
    """
    LSTM модель для прогнозирования uplift на основе временных рядов.

    LSTM (Long Short-Term Memory) — тип рекуррентной нейросети,
    которая умеет «запоминать» важные события из прошлого.

    Архитектура:
        Вход:
        Числовые фичи → LSTM
        Категории → Embedding → Concatenate
               ↓
        LSTM слой (скрытая память)
               ↓
        Полносвязный слой (преобразует память в число)
               ↓
        Выход: прогноз (1 число)

    Где:
        - batch: сколько примеров обрабатываем за раз (например, 32)
        - seq_len: сколько дней истории смотрим (например, 30)
        - input_size: сколько признаков в день (price, discount, ...)
    """

    def __init__(
            self,
            # Числовые параметры
            numeric_features: int,  # количество числовых фич
            categorical_dims: Dict[str, int],  # {имя: размер_словаря}
            embedding_dim: int = 16,  # размер эмбеддинга
            hidden_size: int = 64,  # размер скрытого состояния LSTM
            num_layers: int = 2,  # количество слоёв LSTM
            seq_len: int = 30,
            dropout: float = 0.2,
    ):
        super().__init__()

        self.numeric_features = numeric_features
        self.categorical_dims = categorical_dims
        self.embedding_dim = embedding_dim
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.seq_len = seq_len

        # ===== ЭМБЕДДИНГИ ДЛЯ КАТЕГОРИАЛЬНЫХ ПРИЗНАКОВ =====
        self.embeddings = nn.ModuleDict({
            name: nn.Embedding(dim, embedding_dim)
            for name, dim in categorical_dims.items()
        })

        # ===== LSTM СЛОЙ =====
        # Входной размер = числовые фичи + сумма эмбеддингов
        embedding_total = len(categorical_dims) * embedding_dim
        lstm_input_size = numeric_features + embedding_total

        self.lstm = nn.LSTM(
            input_size=lstm_input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )

        # ===== ПОЛНОСВЯЗНЫЙ СЛОЙ =====
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1)
        )

    def forward(self, x_numeric, x_categorical):
        """
        Args:
            x_numeric: [batch, seq_len, numeric_features]
            x_categorical: [batch, seq_len, num_categorical]

        Returns:
            predictions: [batch]
        """
        batch_size, seq_len = x_numeric.shape[0], x_numeric.shape[1]

        # ===== ПРОГОНЯЕМ КАТЕГОРИИ ЧЕРЕЗ ЭМБЕДДИНГИ =====
        embedded_features = []
        for i, (name, emb_layer) in enumerate(self.embeddings.items()):
            # x_categorical[:, :, i] — колонка для этой категории
            cat_values = x_categorical[:, :, i]  # [batch, seq_len]
            emb = emb_layer(cat_values)  # [batch, seq_len, embedding_dim]
            embedded_features.append(emb)

        # Объединяем все эмбеддинги
        embedded_concat = torch.cat(embedded_features, dim=-1)  # [batch, seq_len, embedding_total]

        # ===== ОБЪЕДИНЯЕМ С ЧИСЛОВЫМИ ФИЧАМИ =====
        lstm_input = torch.cat([x_numeric, embedded_concat], dim=-1)

        # ===== LSTM =====
        lstm_out, (h_n, c_n) = self.lstm(lstm_input)

        # ===== ПОСЛЕДНИЙ ВЫХОД LSTM =====
        last_hidden = h_n[-1]  # [batch, hidden_size]

        # ===== ПРЕДСКАЗАНИЕ =====
        predictions = self.fc(last_hidden)  # [batch, 1]

        return predictions.squeeze(-1)  # [batch]

    def get_config(self) -> dict:
        """Возвращает конфигурацию для сохранения"""
        return {
            "type": "lstm_with_embeddings",
            "numeric_features": self.numeric_features,
            "categorical_dims": self.categorical_dims,
            "embedding_dim": self.embedding_dim,
            "hidden_size": self.hidden_size,
            "num_layers": self.num_layers,
            "seq_len": self.seq_len,
        }

    @classmethod
    def from_config(cls, config: dict):
        """Создаёт модель из конфига (для загрузки)"""
        return cls(
            numeric_features=config.get("numeric_features", 7),
            categorical_dims=config.get("categorical_dims", {}),
            embedding_dim=config.get("embedding_dim", 16),
            hidden_size=config.get("hidden_size", 64),
            num_layers=config.get("num_layers", 2),
            seq_len=config.get("seq_len", 30)
        )