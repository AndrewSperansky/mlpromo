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
    _model = None

    @classmethod
    def load(cls):
        """
        Загружает модель CatBoost/Sklearn из файла.
        Синглтон — загружается только один раз.
        """
        if cls._model is not None:
            return cls._model

        if cls.MODEL_PATH.exists():
            logger.info(f"Loading ML model from {cls.MODEL_PATH}")
            cls._model = joblib.load(cls.MODEL_PATH)
            logger.info("ML model loaded successfully")
        else:
            logger.warning(f"ML model NOT FOUND at {cls.MODEL_PATH}")
            cls._model = None

        return cls._model

    @classmethod
    def reload(cls):
        """
        Принудительная перезагрузка модели (после обучения).
        """
        cls._model = None
        return cls.load()
