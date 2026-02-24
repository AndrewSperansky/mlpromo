# app/ml/model_manager.py

import asyncio
import logging

from app.ml.runtime_state import ML_RUNTIME_STATE
from app.ml.model_loader import ModelLoader

logger = logging.getLogger("promo_ml")


class ModelManager:
    """
    Управляет жизненным циклом ML-модели.
    НЕ знает путь к файлу.
    Использует ModelLoader как источник истины.
    """

    def __init__(self, check_interval: int = 5):
        self.check_interval = check_interval

    def load(self):
        """
        Загружает модель через ModelLoader.
        Обновляет runtime state.
        """
        try:
            result = ModelLoader.load()
            model = result["model"]
            meta = result["meta"]

            if model is None:
                raise RuntimeError("ModelLoader returned None")

            ML_RUNTIME_STATE.update({
                "model_loaded": True,
                "ml_model_id": ML_RUNTIME_STATE.get("ml_model_id"),
                "version": meta.get("version"),
                "feature_order": meta.get("feature_order"),
                "status": "ok",
                "errors": [],
            })

            logger.info(
                "ML model loaded via ModelLoader",
                extra={
                    "ml_model_id": ML_RUNTIME_STATE.get("ml_model_id"),
                    "version": meta.get("version"),
                },
            )

        except Exception as e:
            logger.exception("ModelManager failed to load model")

            ML_RUNTIME_STATE.update({
                "model_loaded": False,
                "status": "error",
                "errors": [str(e)],
            })

            raise

    async def watch(self):
        """
        Watcher: периодически проверяет модель.
        """
        while True:
            try:
                self.load()
                logger.info("ModelManager watcher reloaded model")
            except Exception as e:
                logger.error(
                    "Watcher failed to reload model",
                    extra={"error": str(e)}
                )

            await asyncio.sleep(self.check_interval)