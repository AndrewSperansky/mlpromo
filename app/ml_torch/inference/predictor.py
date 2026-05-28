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
    """Класс для инференса PyTorch моделей с поддержкой эмбеддингов"""

    def __init__(self, db: Session):
        self.db = db
        self.price_service = PriceHistoryService(db)
        self.model = None
        self.model_config = None
        self.numeric_features = None
        self.categorical_features = None

    def load_model(self, model_path: Path, config: dict):
        """
        Загружает сохранённую модель с эмбеддингами
        """

        logger.info(f"📋 Loading model with config: {config}")

        # 🔥 БЕРЁМ ПАРАМЕТРЫ ИЗ КОНФИГА!
        self.model = LSTMUpliftModel(
            numeric_features=config.get("numeric_features", 7),
            categorical_dims=config.get("categorical_dims", {}),
            embedding_dim=config.get("embedding_dim", 16),
            hidden_size=config.get("hidden_size", 64),
            num_layers=config.get("num_layers", 2),
            seq_len=config.get("seq_len", 30)
        )

        checkpoint = torch.load(model_path, map_location='cpu')

        if 'model_state_dict' in checkpoint:
            self.model.load_state_dict(checkpoint['model_state_dict'])
        else:
            self.model.load_state_dict(checkpoint)

        self.model.eval()
        self.model_config = config

        logger.info(f"✅ Модель загружена из {model_path}")
        return self.model

    def predict_next_week_sales(
            self,
            sku: str,
            seq_len: int = 30
    ) -> Optional[float]:
        """
        Предсказывает продажи на следующую неделю
        """
        if self.model is None:
            raise ValueError("Модель не загружена. Вызовите load_model()")

        # TODO: собрать фичи для предсказания
        # Пока возвращаем заглушку
        return None

    def predict_prices_forecast(
            self,
            sku: str,
            days_history: int = 90,
            forecast_days: int = 7,
            seq_len: int = 30
    ) -> List[Dict]:
        """
        Прогнозирует продажи на несколько дней/недель вперёд
        """
        if self.model is None:
            raise ValueError("Модель не загружена")

        # TODO: полноценная реализация с фичами
        # Пока возвращаем заглушку с предсказанием цены из истории
        history = self.price_service.get_retail_price_history(sku, days=days_history)

        if not history:
            return []

        last_price = history[-1]["price"] if history else 0

        predictions = []
        for day in range(1, forecast_days + 1):
            pred_date = date.today() + timedelta(days=day)
            predictions.append({
                "date": pred_date.isoformat(),
                "predicted_sales": round(last_price, 2)  # заглушка
            })

        return predictions