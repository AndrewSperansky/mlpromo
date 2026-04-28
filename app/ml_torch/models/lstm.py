# app/ml_torch/models/lstm.py

import torch
import torch.nn as nn
from typing import Optional, List
from .base import BaseTorchModel


class LSTMUpliftModel(BaseTorchModel):
    """
    LSTM модель для прогнозирования uplift на основе временных рядов.

    LSTM (Long Short-Term Memory) — тип рекуррентной нейросети,
    которая умеет «запоминать» важные события из прошлого.

    Архитектура:
        Вход: [batch, seq_len, input_size]
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
            # ===== ОСНОВНЫЕ ПАРАМЕТРЫ =====
            input_size: int = 1,  # количество признаков (price, sales...) — РАЗМЕР ВХОДА
            hidden_size: int = 64,  # размер скрытого состояния — «ВМЕСТИЛИЩЕ ПАМЯТИ»
            num_layers: int = 2,  # количество слоёв LSTM — «ГЛУБИНА ЗАПОМИНАНИЯ»
            dropout: float = 0.2,  # регуляризация — «ЗАБЫВАНИЕ» случайных нейронов

            # ===== ПАРАМЕТРЫ ВЫХОДНОГО СЛОЯ =====
            fc_hidden_dims: List[int] = [32, 16],  # размеры полносвязных слоёв
            output_dim: int = 1,  # сколько чисел выдаём (1 = uplift)

            # ===== ПАРАМЕТРЫ ОБУЧЕНИЯ (по умолчанию) =====
            learning_rate: float = 0.001,  # скорость обучения («шаг» градиентного спуска)
            batch_size: int = 32,  # размер батча («порция» примеров)
            seq_len: int = 30,  # длина последовательности («окно истории»)
    ):
        super().__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.input_size = input_size
        self.seq_len = seq_len
        self.learning_rate = learning_rate
        self.batch_size = batch_size

        # ===== LSTM СЛОЙ =====
        # batch_first=True означает: вход [batch, seq_len, features]
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )

        # ===== ПОЛНОСВЯЗНЫЕ СЛОИ (преобразуют память в ответ) =====
        layers = []
        prev_size = hidden_size

        for h_dim in fc_hidden_dims:
            layers.extend([
                nn.Linear(prev_size, h_dim),
                nn.ReLU(),  # функция активации (пропускает только положительные числа)
                nn.Dropout(dropout)  # случайное выключение нейронов
            ])
            prev_size = h_dim

        layers.append(nn.Linear(prev_size, output_dim))
        self.fc = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Прямой проход (forward pass) — превращаем вход в выход.

        x: [batch, seq_len, input_size]
           batch: сколько примеров
           seq_len: сколько дней истории
           input_size: сколько признаков в день

        Returns:
            predictions: [batch] — прогноз для каждого примера
        """
        # LSTM обрабатывает последовательность
        # lstm_out: [batch, seq_len, hidden_size] — выходы на каждый момент
        # (h_n, c_n) — финальное скрытое и клеточное состояние
        lstm_out, (h_n, c_n) = self.lstm(x)

        # Берём последнее скрытое состояние (оно содержит «память» о всей последовательности)
        # h_n[-1] — последний слой LSTM
        last_hidden = h_n[-1]  # [batch, hidden_size]

        # Полносвязные слои превращают память в прогноз
        predictions = self.fc(last_hidden)  # [batch, output_dim]

        # Убираем лишнюю размерность: [batch, 1] -> [batch]
        return predictions.squeeze(-1)

    def get_config(self) -> dict:
        """Возвращает конфигурацию модели для сохранения в meta.json"""
        return {
            "type": "lstm",
            "input_size": self.input_size,
            "hidden_size": self.hidden_size,
            "num_layers": self.num_layers,
            "seq_len": self.seq_len,
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size
        }

    @classmethod
    def from_config(cls, config: dict):
        """Создаёт модель из конфига (для загрузки)"""
        return cls(
            input_size=config.get("input_size", 1),
            hidden_size=config.get("hidden_size", 64),
            num_layers=config.get("num_layers", 2),
            seq_len=config.get("seq_len", 30)
        )