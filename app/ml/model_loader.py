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

    MODEL_PATH = Path("data/models_history/latest_model.pkl")
    META_PATH = Path("data/models_history/latest_model.meta.json")

    _model = None
    _meta = None

    @classmethod
    def load(cls):
        """
        Загружает ML-модель и метаданные.
        Возвращает dict: {"model": ..., "meta": {...}}
        """
        # already loaded (singleton)
        if cls._model is not None and cls._meta is not None:
            return {"model": cls._model, "meta": cls._meta}

        if not cls.MODEL_PATH.exists():
            logger.warning("ML model NOT FOUND at %s", cls.MODEL_PATH)
            cls._model = None
            cls._meta = {"feature_order": []}
            return {"model": cls._model, "meta": cls._meta}

        # Load model safely
        try:
            logger.info("Loading ML model from %s", cls.MODEL_PATH)
            cls._model = joblib.load(cls.MODEL_PATH)
        except Exception as e:
            logger.error("Failed to load ML model: %s", e)
            cls._model = None

        # Load meta safely
        if cls.META_PATH.exists():
            try:
                cls._meta = json.loads(cls.META_PATH.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Meta file corrupted: %s", e)
                cls._meta = {"feature_order": []}
        else:
            cls._meta = {"feature_order": []}

        logger.info("ML model loaded successfully")
        return {"model": cls._model, "meta": cls._meta}

    @classmethod
    def reload(cls):
        """
        Принудительная перезагрузка модели (после обучения).
        """
        cls._model = None
        cls._meta = None
        return cls.load()
