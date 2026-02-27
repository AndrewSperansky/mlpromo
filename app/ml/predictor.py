# app/ml/predictor.py

import time
from pathlib import Path
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.ml.registry.service import ModelRegistryService
from models.ml_model import MLModelManager
from app.ml.monitoring.inference_metrics import collect_inference_metrics


class Predictor:

    def __init__(self, model_name: str = "promo_uplift"):
        self.model_name = model_name
        self.model = None
        self.meta = None

        self._load_active_model()

    def _load_active_model(self):

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

    def predict(self, X):

        start = time.perf_counter()

        preds = self.model.predict(X)

        latency_ms = (time.perf_counter() - start) * 1000

        collect_inference_metrics(
            ml_model_id=self.meta["ml_model_id"],
            inputs=X,
            outputs=preds,
            latency_ms=latency_ms,
        )

        return preds