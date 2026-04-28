# app/ml_torch/inference/predictor.py

import torch
import logging
from pathlib import Path
from typing import Optional, List, Dict
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.services.price_history_service import PriceHistoryService
from app.ml_torch.models.lstm import LSTMUpliftModel

logger = logging.getLogger("promo_ml")


class TorchPredictor:
    """
    Класс для инференса (предсказания) PyTorch моделей.

    Инференс (inference) — процесс получения прогноза от обученной модели.
    """

    def __init__(self, db: Session):
        self.db = db
        self.price_service = PriceHistoryService(db)
        self.model = None
        self.model_config = None

    def load_model(self, model_path: Path, config: dict):
        """
        Загружает сохранённую модель

        Args:
            model_path: путь к .pt файлу
            config: конфигурация модели (input_size, hidden_size, ...)
        """
        self.model = LSTMUpliftModel.from_config(config)

        checkpoint = torch.load(model_path, map_location='cpu')

        # Извлекаем только веса модели (без оптимизатора)
        if 'model_state_dict' in checkpoint:
            self.model.load_state_dict(checkpoint['model_state_dict'])
        else:
            self.model.load_state_dict(checkpoint)

        self.model.eval()  # переводим в режим оценки (отключаем dropout)
        self.model_config = config

        logger.info(f"Модель загружена из {model_path}")
        return self.model

    def predict_next_price(
            self,
            sku: str,
            days: int = 30,
            seq_len: int = 30
    ) -> Optional[float]:
        """
        Предсказывает следующую цену на основе истории

        Args:
            sku: артикул
            days: сколько дней истории брать
            seq_len: длина окна (должна совпадать с обученной)
        """
        if self.model is None:
            raise ValueError("Модель не загружена. Вызовите load_model()")

        # Загружаем историю цен
        history = self.price_service.get_retail_price_history(sku, days=days)

        if len(history) < seq_len:
            logger.warning(f"Недостаточно данных для SKU={sku}: нужно {seq_len}, есть {len(history)}")
            return None

        # Берём последние seq_len значений
        last_prices = [h["price"] for h in history[-seq_len:]]

        # Преобразуем в тензор: [1, seq_len, input_size]
        import numpy as np
        input_tensor = torch.tensor(last_prices, dtype=torch.float32).view(1, seq_len, 1)

        # Предсказание
        with torch.no_grad():
            prediction = self.model(input_tensor)

        return float(prediction.numpy()[0])

    def predict_prices_forecast(
            self,
            sku: str,
            days_history: int = 90,
            forecast_days: int = 7,
            seq_len: int = 30
    ) -> List[Dict]:
        """
        Прогнозирует цены на несколько дней вперёд (авторегрессия)

        Принцип: предсказываем следующий день, добавляем его в историю,
        и повторяем для следующего дня.

        Args:
            sku: артикул
            days_history: сколько дней истории брать
            forecast_days: на сколько дней вперёд прогноз
            seq_len: длина окна модели
        """
        if self.model is None:
            raise ValueError("Модель не загружена")

        # Загружаем историю
        history = self.price_service.get_retail_price_history(sku, days=days_history)

        if len(history) < seq_len:
            raise ValueError(f"Недостаточно данных: нужно {seq_len}, есть {len(history)}")

        # Берём последние seq_len цен как начальную последовательность
        prices = [h["price"] for h in history]

        predictions = []
        current_prices = prices[-seq_len:].copy()

        for day in range(1, forecast_days + 1):
            # Формируем вход
            input_tensor = torch.tensor(current_prices, dtype=torch.float32).view(1, seq_len, 1)

            # Предсказываем
            with torch.no_grad():
                next_price = float(self.model(input_tensor).numpy()[0])

            # Сохраняем
            pred_date = date.today() + timedelta(days=day)
            predictions.append({
                "date": pred_date.isoformat(),
                "predicted_price": round(next_price, 2)
            })

            # Добавляем в последовательность для следующего шага
            current_prices.pop(0)
            current_prices.append(next_price)

        return predictions