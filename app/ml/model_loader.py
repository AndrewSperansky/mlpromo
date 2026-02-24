# app/ml/model_loader.py

import logging
from pathlib import Path
from app.ml.runtime_state import ML_RUNTIME_STATE
import json
from app.core.settings import settings
from catboost import CatBoostRegressor


logger = logging.getLogger("promo_ml")


class ModelLoader:
    """
    Глобальный загрузчик ML-модели.
    Кэширует модель и метаданные после первого чтения.
    """

    _model = None
    _meta = None
    _loaded_model_id = None

    @classmethod
    def _resolve_model_path(cls) -> Path:
        """
        Динамически формирует путь к модели
        на основе текущего ML_RUNTIME_STATE.
        """
        model_id = ML_RUNTIME_STATE.get("ml_model_id")
        model_filename = f"{model_id}.cbm"
        model_path = Path(settings.ML_MODEL_DIR) / model_filename

        ML_RUNTIME_STATE["contract"]["model_path"] = str(model_path)

        return model_path

    @classmethod
    def load(cls):
        """
        Загружает ML-модель и метаданные.
        Возвращает dict: {"model": ..., "meta": {...}}
        """

        current_model_id = ML_RUNTIME_STATE.get("ml_model_id")

        # Если модель уже загружена и id совпадает — возвращаем кэш
        if (
            cls._model is not None
            and cls._meta is not None
            and cls._loaded_model_id == current_model_id
        ):
            return {"model": cls._model, "meta": cls._meta}

        model_path = cls._resolve_model_path()

        if not model_path.exists():
            logger.warning("ML model NOT FOUND at %s", model_path)
            cls._model = None
            cls._meta = {"feature_order": []}
            cls._loaded_model_id = None
            return {"model": cls._model, "meta": cls._meta}

        # ===============  Load model safely  ===========================
        try:
            logger.info("Loading CatBoost model from %s", model_path)
            model = CatBoostRegressor()
            model.load_model(str(model_path), format="cbm")
            cls._model = model
            cls._loaded_model_id = current_model_id
        except Exception as e:
            logger.error("Failed to load CatBoost model: %s", e)
            cls._model = None
            cls._loaded_model_id = None

        # ===============  Load meta safely  =============================
        meta_path = Path(settings.ML_META_PATH)

        if meta_path.exists():
            try:
                cls._meta = json.loads(
                    meta_path.read_text(encoding="utf-8")
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
        cls._loaded_model_id = None
        return cls.load()