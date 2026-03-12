# app/ml/model_loader.py

import logging
from pathlib import Path
from app.ml.runtime_state import ML_RUNTIME_STATE
import json
from app.core.settings import settings
from catboost import CatBoostRegressor
from app.db.session import SessionLocal
from models.ml_model import MLModel

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
        # 1. Проверяем, есть ли сохранённый путь в runtime
        saved_path = ML_RUNTIME_STATE.get("model_path")
        if saved_path:
            path = Path(saved_path)
            if path.exists():
                return path

        # 2. Получаем model_id
        model_id = ML_RUNTIME_STATE.get("ml_model_id")

        # 3. Если это число — ищем в БД
        if isinstance(model_id, int):
            db = SessionLocal()
            try:
                model_record = db.query(MLModel).filter(MLModel.id == model_id).first()
                if model_record and model_record.model_path:
                    path = Path(model_record.model_path)
                    if path.exists():
                        # Сохраняем для будущих загрузок
                        ML_RUNTIME_STATE["model_path"] = str(path)
                        return path
            except Exception as e:
                logger.error(f"Error querying model from DB: {e}")
            finally:
                db.close()

        # 4. Для старых моделей (cb_promo_v1) — старая логика
        model_path = Path(settings.ML_MODEL_DIR) / f"{model_id}.cbm"

        # Пробуем также в подпапках
        if not model_path.exists():
            alt_path = Path(settings.ML_MODEL_DIR) / "current" / f"{model_id}.cbm"
            if alt_path.exists():
                model_path = alt_path

        if not model_path.exists():
            alt_path = Path(settings.ML_MODEL_DIR) / "archive" / f"{model_id}.cbm"
            if alt_path.exists():
                model_path = alt_path

        # Сохраняем в contract для обратной совместимости
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

            # Сохраняем путь для будущих загрузок
            ML_RUNTIME_STATE["model_path"] = str(model_path)

        except Exception as e:
            logger.error("Failed to load CatBoost model: %s", e)
            cls._model = None
            cls._loaded_model_id = None

        # ===============  Load meta safely  =============================
        # Пробуем найти meta.json рядом с моделью
        meta_path = model_path.with_suffix('.meta.json')

        if not meta_path.exists():
            # Если нет — пробуем старый путь из настроек
            meta_path = Path(settings.ML_META_PATH)

        if meta_path.exists():
            try:
                cls._meta = json.loads(meta_path.read_text(encoding="utf-8"))
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