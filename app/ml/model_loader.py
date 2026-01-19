# app/ml/model_loader.py

import logging
from pathlib import Path
import joblib
import json

logger = logging.getLogger("promo_ml")


class ModelLoader:
    """
    Глобальный загрузчик ML-модели.
    Кэширует модель и метаданные после первого чтения.
    """

    MODEL_PATH = Path("/app/models/baseline_catboost.pkl")
    META_PATH = Path("app/models/baseline_catboost.meta.json")

    @classmethod
    def load(cls):
        """
        Загружает ML-модель и метаданные.
        Возвращает dict: {"model": ..., "meta": {...}}
        """

        if not cls.MODEL_PATH.exists():
            logger.warning("ML model NOT FOUND at %s", cls.MODEL_PATH)
            return {"model": None, "meta": {"feature_order": []}}

        # ===============  Load model safely  ===========================
        try:
            logger.info("Loading ML model from %s", cls.MODEL_PATH)
            model = joblib.load(cls.MODEL_PATH)
        except Exception as e:
            logger.error("Failed to load ML model: %s", e)
            model = None

        # ===============  Load meta safely  =============================
        if cls.META_PATH.exists():
            try:
                meta = json.loads(cls.META_PATH.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Meta file corrupted: %s", e)
                meta = {"feature_order": []}
        else:
            meta = {"feature_order": []}

        return {"model": model, "meta": meta}


