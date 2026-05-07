# app/ml_torch/train/train_pipeline.py

"""
LSTM training pipeline — обучение нейросети на временных рядах.
"""

import json
import logging
import torch
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session
from torch.utils.data import DataLoader, random_split

from app.db.session import SessionLocal
from app.core.settings import settings
from app.services.registry_service import ModelRegistryService
from app.services.price_history_service import PriceHistoryService
from app.ml_torch.models.lstm import LSTMUpliftModel
from app.ml_torch.train.trainer import TorchTrainer
from app.ml_torch.data.dataset import UpliftTimeSeriesDataset

logger = logging.getLogger("promo_ml")


def train_lstm_pipeline(
        sku: str,
        days: int = 365,
        seq_len: int = 30,
        hidden_size: int = 64,
        num_layers: int = 2,
        learning_rate: float = 0.001,
        batch_size: int = 32,
        epochs: int = 50,
        promote: bool = False
) -> dict:
    """
    Обучает LSTM модель для конкретного SKU.
    """
    logger.info(f"🚀 Запуск LSTM обучения для SKU={sku}")

    db = SessionLocal()
    try:
        # ===== 1. ЗАГРУЖАЕМ ИСТОРИЮ ЦЕН =====
        price_service = PriceHistoryService(db)
        price_history = price_service.get_retail_price_history(sku, days=days)

        if len(price_history) < seq_len + 1:
            raise ValueError(
                f"Недостаточно данных для SKU={sku}: "
                f"нужно {seq_len + 1} дней, есть {len(price_history)}"
            )

        # ===== 2. ГОТОВИМ DATAFRAME =====
        df = pd.DataFrame(price_history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Создаём целевую переменную (next_day_price)
        df['next_day_price'] = df['price'].shift(-1)
        df = df.dropna()

        # ===== 3. СОЗДАЁМ DATASET =====
        feature_cols = ['price']
        target_col = 'next_day_price'

        dataset = UpliftTimeSeriesDataset(
            df=df,
            feature_cols=feature_cols,
            target_col=target_col,
            seq_len=seq_len
        )

        # ===== 4. РАЗДЕЛЯЕМ НА ОБУЧЕНИЕ И ВАЛИДАЦИЮ =====
        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        # ===== 5. СОЗДАЁМ МОДЕЛЬ =====
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Используем устройство: {device}")

        model = LSTMUpliftModel(
            input_size=len(feature_cols),
            hidden_size=hidden_size,
            num_layers=num_layers,
            seq_len=seq_len,
            learning_rate=learning_rate,
            batch_size=batch_size
        )

        # ===== 6. ОБУЧАЕМ =====
        trainer = TorchTrainer(
            model=model,
            learning_rate=learning_rate,
            device=device
        )

        train_result = trainer.train(
            train_dataloader=train_loader,
            val_dataloader=val_loader,
            epochs=epochs,
            early_stopping_patience=10
        )

        # ===== 7. СОХРАНЯЕМ МОДЕЛЬ =====
        candidate_dir = Path(settings.ML_CANDIDATE_DIR)
        candidate_dir.mkdir(parents=True, exist_ok=True)

        model_id = int(datetime.now(timezone.utc).timestamp())
        model_path = candidate_dir / f"lstm_{sku}_{model_id}.pt"

        trainer.save_checkpoint(str(model_path))

        # ===== 8. РЕГИСТРИРУЕМ В БД =====
        registry = ModelRegistryService(db)

        db_model = registry.register_model(
            name=f"lstm_uplift_{sku}",
            version=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S'),
            algorithm="pytorch_lstm",
            model_type="time_series",
            target="next_day_price",
            features=feature_cols,
            metrics={"val_loss": train_result["best_val_loss"]},
            model_path=model_path,
            trained_rows_count=len(dataset)
        )

        # ===== 8.1 СОХРАНЯЕМ КОНФИГУРАЦИЮ МОДЕЛИ =====
        model_config = {
            "type": "lstm",
            "input_size": len(feature_cols),
            "hidden_size": hidden_size,
            "num_layers": num_layers,
            "seq_len": seq_len,
            "learning_rate": learning_rate,
            "batch_size": batch_size
        }

        # ===== 8.2 СОХРАНЯЕМ meta.json =====
        meta = {
            "model_id": db_model.id,
            "model_name": f"lstm_uplift_{sku}",
            "algorithm": "pytorch_lstm",
            "model_config": model_config,
            "metrics": {"val_loss": train_result["best_val_loss"]},
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "total_rows": len(dataset),
            "sku_code": sku
        }

        meta_path = candidate_dir / f"{db_model.id}.meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        # ===== 9. ПРОМОУШН =====
        promoted = False
        if promote:
            registry.promote_model(db_model.id)
            promoted = True
            logger.info(f"🎉 Модель {db_model.id} активирована")

        return {
            "status": "success",
            "model_id": db_model.id,
            "sku": sku,
            "val_loss": train_result["best_val_loss"],
            "epochs_completed": train_result["epochs_completed"],
            "promoted": promoted
        }

    except Exception as e:
        logger.error(f"Ошибка обучения LSTM для SKU {sku}: {e}")
        return {
            "status": "error",
            "sku": sku,
            "error": str(e)
        }
    finally:
        db.close()