# app/ml/predictor.py

import time
from pathlib import Path
from sqlalchemy.orm import Session
# from typing import Optional

from app.db.session import SessionLocal
from services.registry_service import ModelRegistryService
from models.ml_model import MLModelManager, MLModel  # ← добавили импорт MLModel
from app.ml.monitoring.inference_metrics import collect_inference_metrics


class Predictor:

    def __init__(self, model_name: str = "promo_uplift"):
        self.model_name = model_name
        self.model = None
        self.meta = None

        self._load_active_model()

    def _load_active_model(self):
        """Загружает активную модель (для production)"""
        db: Session = SessionLocal()

        try:
            registry = ModelRegistryService(db)
            active_model = registry.get_active_model(self.model_name)

            if not active_model:
                raise RuntimeError("No active model found in registry")

            manager = MLModelManager(Path(active_model.model_path))

            if not manager.load():
                raise RuntimeError("Failed to load model file")

            self.model = manager.model
            self.meta = {
                "ml_model_id": active_model.id,
                "version": active_model.version,
            }

        finally:
            db.close()

    # ===== НОВЫЙ МЕТОД для Evaluate =====
    def load_by_id(self, model_record: MLModel) -> bool:
        """
        Загружает модель по объекту модели из БД.
        Используется для evaluate, где модель уже получена.
        """
        manager = MLModelManager(Path(model_record.model_path))

        if not manager.load():
            return False

        self.model = manager.model
        self.meta = {
            "ml_model_id": model_record.id,
            "version": model_record.version,
            "features": model_record.features,
            "target": model_record.target
        }
        return True

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