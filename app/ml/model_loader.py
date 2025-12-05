import logging
from pathlib import Path
import joblib

logger = logging.getLogger("promo_ml")


class ModelLoader:
    """
    Глобальный загрузчик ML-модели.
    Кэширует модель после первого чтения.
    """

    MODEL_PATH = Path("data/models_history/latest_model.pkl")
    META_PATH = Path("data/models_history/latest_model.meta.json")

    _model = None
    _meta = None

    @classmethod
    def load(cls):
        """
        Загружает модель CatBoost/Sklearn из файла.
        Синглтон — загружается только один раз.
        """
        if cls._model is not None:
            return cls._model, cls._meta

        if cls.MODEL_PATH.exists():
            logger.info(f"Loading ML model from {cls.MODEL_PATH}")
            cls._model = joblib.load(cls.MODEL_PATH)
            if cls.META_PATH.exists():
                import json

                cls._meta = json.loads(cls.META_PATH.read_text(encoding="utf-8"))
            else:
                cls._meta = {"feature_order": []}

            logger.info("ML model loaded successfully")
        else:
            logger.warning(f"ML model NOT FOUND at {cls.MODEL_PATH}")
            cls._model, cls._meta = None, {"feature_order": []}

        return cls._model, cls._meta

    @classmethod
    def reload(cls):
        """
        Принудительная перезагрузка модели (после обучения).
        """
        cls._model = None
        return cls.load()
