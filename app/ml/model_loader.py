# app/ml/model_loader.py

import logging
from pathlib import Path
import joblib
import json
from app.core.settings import settings
from catboost import CatBoostRegressor


logger = logging.getLogger("promo_ml")


class ModelLoader:
    """
    Глобальный загрузчик ML-модели.
    Кэширует модель и метаданные после первого чтения.
    """

    MODEL_PATH = Path(settings.ML_MODEL_PATH)
    META_PATH = Path(settings.ML_META_PATH)

    _model = None
    _meta = None

    @classmethod
    def load(cls):
        """
        Загружает ML-модель и метаданные.
        Возвращает dict: {"model": ..., "meta": {...}}
        """
        if cls._model is not None and cls._meta is not None:
            return {"model": cls._model, "meta": cls._meta}

        if not cls.MODEL_PATH.exists():
            logger.warning("ML model NOT FOUND at %s", cls.MODEL_PATH)
            cls._model = None
            cls._meta = {"feature_order": []}
            return {"model": cls._model, "meta": cls._meta}

        # ===============  Load model safely  ===========================
        try:
            logger.info("Loading CatBoost model from %s", cls.MODEL_PATH)
            model = CatBoostRegressor()
            model.load_model(str(cls.MODEL_PATH), format="cbm")
            cls._model = model
        except Exception as e:
            logger.error("Failed to load CatBoost model: %s", e)
            cls._model = None

        # ===============  Load meta safely  =============================
        if cls.META_PATH.exists():
            try:
                cls._meta = json.loads(
                    cls.META_PATH.read_text(encoding="utf-8")
                )
            except Exception as e:
                logger.warning("Meta file corrupted: %s", e)
                cls._meta = {"feature_order": []}
        else:
            cls._meta = {"feature_order": []}

        return {"model": cls._model, "meta": cls._meta}

    @classmethod
    def reload(cls):
        cls._model = None
        cls._meta = None
        return cls.load()


