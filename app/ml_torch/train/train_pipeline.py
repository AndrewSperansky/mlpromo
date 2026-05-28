# app/ml_torch/train/train_pipeline.py

"""
LSTM training pipeline — обучение нейросети на временных рядах с эмбеддингами.
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
from app.ml_torch.train.trainer_with_embeddings import TorchTrainerWithEmbeddings
from app.ml_torch.data.dataset import UpliftTimeSeriesDataset
from app.ml_torch.features.feature_builder import FeatureBuilder

logger = logging.getLogger("promo_ml")


def train_lstm_pipeline(
    sku: str,
    days: int = 365,
    seq_len: int = 30,
    hidden_size: int = 64,
    num_layers: int = 2,
    embedding_dim: int = 16,
    learning_rate: float = 0.001,
    batch_size: int = 32,
    epochs: int = 50,
    promote: bool = False
) -> dict:
    """
    Обучает LSTM модель для конкретного SKU с использованием:
    - числовых фич (цены, продажи, лаги)
    - категориальных фич (через эмбеддинги)
    """
    logger.info(f"🚀 Запуск LSTM обучения для SKU={sku}")

    db = SessionLocal()
    try:
        # ===== 1. СТРОИМ ФИЧИ =====
        feature_builder = FeatureBuilder(db)
        df = feature_builder.build_features_for_sku(sku, days)

        if df.empty:
            raise ValueError(f"Нет данных для SKU={sku}")

        logger.info(f"📊 Загружено {len(df)} строк с фичами")

        # ===== 2. ОПРЕДЕЛЯЕМ ЦЕЛЕВУЮ ПЕРЕМЕННУЮ =====
        # Предсказываем продажи на следующей неделе (или quantity)
        df['target'] = df['quantity'].shift(-1)
        df = df.dropna().reset_index(drop=True)

        if len(df) < seq_len + 1:
            raise ValueError(
                f"Недостаточно данных: нужно {seq_len + 1} строк, "
                f"после подготовки target осталось {len(df)}"
            )

        # ===== 3. СОЗДАЁМ DATASET =====
        numeric_features = feature_builder.numeric_features
        categorical_features = feature_builder.categorical_features

        dataset = UpliftTimeSeriesDataset(
            df=df,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
            target_col='target',
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
        logger.info(f"💻 Используем устройство: {device}")

        model = LSTMUpliftModel(
            numeric_features=len(numeric_features),
            categorical_dims=dataset.get_embedding_dims(),
            embedding_dim=embedding_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            seq_len=seq_len
        )

        # ===== 6. ОБУЧАЕМ =====
        trainer = TorchTrainerWithEmbeddings(
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

        # Генерируем ID модели (можно и из БД, но сначала сохраняем)
        timestamp = int(datetime.now(timezone.utc).timestamp())
        model_filename = f"lstm_{sku}_{timestamp}.pt"
        model_path = candidate_dir / model_filename

        trainer.save_checkpoint(str(model_path))

        # ===== 8. РЕГИСТРИРУЕМ В БД =====
        registry = ModelRegistryService(db)

        # Сохраняем конфигурацию эмбеддингов
        embedding_config = dataset.get_embedding_dims()

        db_model = registry.register_model(
            name=f"lstm_uplift_{sku}",
            version=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S'),
            algorithm="pytorch_lstm_with_embeddings",
            model_type="time_series",
            target="next_week_sales",
            features=numeric_features + categorical_features,
            metrics={"val_loss": train_result["best_val_loss"]},
            model_path=model_path,
            trained_rows_count=len(dataset)
        )

        # ===== 8.1 СОХРАНЯЕМ КОНФИГУРАЦИЮ МОДЕЛИ =====
        model_config = {
            "type": "lstm_with_embeddings",
            "numeric_features": len(numeric_features),
            "categorical_dims": embedding_config,
            "embedding_dim": embedding_dim,
            "hidden_size": hidden_size,
            "num_layers": num_layers,
            "seq_len": seq_len,
            "learning_rate": learning_rate,
            "batch_size": batch_size,
            "label_encoders": dataset.get_label_encoders_serializable()
        }

        # ===== 8.2 СОХРАНЯЕМ meta.json =====
        meta = {
            "model_id": db_model.id,
            "model_name": f"lstm_uplift_{sku}",
            "algorithm": "pytorch_lstm_with_embeddings",
            "model_config": model_config,
            "metrics": {"val_loss": train_result["best_val_loss"]},
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "total_rows": len(dataset),
            "sku_code": sku,
            "numeric_features": numeric_features,
            "categorical_features": categorical_features,
        }

        meta_path = candidate_dir / f"{db_model.id}.meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        # Обновляем путь в БД (если нужно переместить)
        db_model.model_path = str(model_path)
        db.commit()

        # ===== 9. ПРОМОУШН =====
        promoted = False
        if promote:
            try:
                registry.promote_model(db_model.id)
                promoted = True
                logger.info(f"🎉 Модель {db_model.id} активирована")
            except Exception as e:
                logger.warning(f"Promotion failed: {e}")

        return {
            "status": "success",
            "model_id": db_model.id,
            "sku": sku,
            "val_loss": train_result["best_val_loss"],
            "epochs_completed": train_result["epochs_completed"],
            "promoted": promoted
        }

    except Exception as e:
        logger.error(f"Ошибка обучения LSTM для SKU {sku}: {e}", exc_info=True)
        return {
            "status": "error",
            "sku": sku,
            "error": str(e)
        }
    finally:
        db.close()