# app/ml/predictor.py

import logging
import time
from pathlib import Path
from sqlalchemy.orm import Session
# from typing import Optional

from app.db.session import SessionLocal
from app.services.registry_service import ModelRegistryService
from models.ml_model import MLModelManager, MLModel  # ← добавили импорт MLModel
from app.ml.monitoring.inference_metrics import collect_inference_metrics

logger = logging.getLogger(__name__)


class Predictor:

    def __init__(self, model_name: str = "promo_uplift"):
        self.model_name = model_name
        self.model = None
        self.meta = None
        self.model_record = None

        # self._load_active_model()  # НЕ вызываем _load_active_model() здесь!

    def _load_active_model(self):
        """Загружает активную модель (для production)"""
        db: Session = SessionLocal()

        try:
            registry = ModelRegistryService(db)
            active_model = registry.get_active_model(self.model_name)

            if not active_model:
                raise RuntimeError("No active model found in registry")

            self._load_model_from_record(active_model)

        finally:
            db.close()

    # ===== НОВЫЙ МЕТОД ======

    def _load_model_from_record(self, model_record: MLModel):
        """Загружает модель по записи из БД"""
        manager = MLModelManager(Path(model_record.model_path))
        if not manager.load():
            raise RuntimeError(f"Failed to load model file: {model_record.model_path}")

        self.model = manager.model
        self.model_record = model_record
        self.meta = {
            "ml_model_id": model_record.id,
            "version": model_record.version,
            "features": model_record.features,
            "target": model_record.target
        }



    # ===== НОВЫЙ МЕТОД для Evaluate =====
    def load_by_id(self, model_record: MLModel) -> bool:
        """
        Загружает модель по объекту модели из БД.
        Используется для evaluate, где модель уже получена.
        """
        manager = MLModelManager(Path(model_record.model_path))

        try:
            self._load_model_from_record(model_record)
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def predict(self, X, collect_metrics: bool = True):
        """
        Делает предсказание.

        Args:
            X: признаки
            collect_metrics: собирать ли метрики инференса (для evaluation = False)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        start = time.perf_counter()
        preds = self.model.predict(X)
        latency_ms = (time.perf_counter() - start) * 1000

        if collect_metrics and self.meta:
            collect_inference_metrics(
                ml_model_id=self.meta["ml_model_id"],
                inputs=X,
                outputs=preds,
                latency_ms=latency_ms,
            )

        return preds

    def get_metadata(self):
        """Возвращает метаданные модели"""
        return self.meta