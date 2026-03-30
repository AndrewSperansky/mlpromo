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

        Приоритет:
        1. Сохранённый путь в runtime state (model_path)
        2. Путь из БД для модели с ID (число)
        3. Поиск в стандартных папках (current, archive, _candidate)
        4. Старая логика (прямой путь)
        """


        # ===== 1. Проверяем сохранённый путь в runtime =====
        saved_path = ML_RUNTIME_STATE.get("model_path")
        if saved_path:
            path = Path(saved_path)
            if path.exists():
                logger.debug(f"Using saved model path: {path}")
                return path
            else:
                logger.warning(f"Saved model path does not exist: {path}")

        # ===== 2. Получаем model_id =====
        model_id = ML_RUNTIME_STATE.get("ml_model_id")

        # ===== 3. Если это число — ищем в БД =====
        if isinstance(model_id, int):
            try:
                from app.db.session import SessionLocal
                from models.ml_model import MLModel

                db = SessionLocal()
                try:
                    model_record = db.query(MLModel).filter(MLModel.id == model_id).first()
                    if model_record and model_record.model_path:
                        path = Path(model_record.model_path)
                        if path.exists():
                            # Сохраняем для будущих загрузок
                            ML_RUNTIME_STATE["model_path"] = str(path)
                            logger.info(f"Found model in DB, path: {path}")
                            return path
                        else:
                            logger.warning(f"Model path from DB does not exist: {path}")
                    else:
                        logger.warning(f"Model {model_id} not found in DB or has no path")
                except Exception as e:
                    logger.error(f"Error querying model from DB: {e}")
                finally:
                    db.close()
            except ImportError as e:
                logger.error(f"Failed to import DB modules: {e}")

        # ===== 4. Для старых моделей (строковые ID) — ищем в стандартных папках =====
        # Пробуем разные варианты
        possible_paths = [
            Path(settings.ML_MODEL_DIR) / f"{model_id}.cbm",
            Path(settings.ML_MODEL_DIR) / "current" / f"{model_id}.cbm",
            Path(settings.ML_MODEL_DIR) / "archive" / f"{model_id}.cbm",
            Path(settings.ML_MODEL_DIR) / "_candidate" / f"{model_id}.cbm",
        ]

        # Также пробуем найти по дате, если model_id похож на дату
        if isinstance(model_id, str) and "T" in model_id:
            # Ищем в _candidate файлы с похожей датой
            candidate_dir = Path(settings.ML_MODEL_DIR) / "_candidate"
            if candidate_dir.exists():
                # Ищем файлы, начинающиеся с даты (первые 10 символов)
                date_part = model_id[:10] if len(model_id) >= 10 else ""
                if date_part:
                    matching = list(candidate_dir.glob(f"{date_part}*.cbm"))
                    if matching:
                        possible_paths.append(matching[0])

        for path in possible_paths:
            if path.exists():
                logger.info(f"Found model at: {path}")
                # Сохраняем для будущих загрузок
                ML_RUNTIME_STATE["model_path"] = str(path)
                # Также сохраняем в contract для обратной совместимости
                if "contract" in ML_RUNTIME_STATE:
                    ML_RUNTIME_STATE["contract"]["model_path"] = str(path)
                return path

        # ===== 5. Если ничего не нашли — возвращаем путь по умолчанию для ошибки =====
        default_path = Path(settings.ML_MODEL_DIR) / f"{model_id}.cbm"
        logger.warning(f"Model not found, returning default path: {default_path}")

        # Сохраняем в contract для обратной совместимости
        if "contract" in ML_RUNTIME_STATE:
            ML_RUNTIME_STATE["contract"]["model_path"] = str(default_path)

        return default_path

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
            ML_RUNTIME_STATE["model_path"] = str(model_path)
        except Exception as e:
            logger.error("Failed to load CatBoost model: %s", e)
            cls._model = None
            cls._loaded_model_id = None

        # ===============  Load meta from RUNTIME STATE ===============
        # Берём из runtime, а не из файла!
        feature_order = ML_RUNTIME_STATE.get("feature_order", [])
        version = ML_RUNTIME_STATE.get("version")

        # также пытаемся загрузить из файла метаданных
        meta_path = model_path.with_suffix('.meta.json')
        if meta_path.exists():
            try:
                with open(meta_path) as f:
                    file_meta = json.load(f)
                    if not feature_order:
                        feature_order = file_meta.get("feature_order", [])
                    if not version:
                        version = file_meta.get("version")
            except Exception as e:
                logger.warning(f"Failed to load meta file: {e}")

        #  создаём метаданные
        cls._meta = {
            "feature_order": feature_order,
            "version": version,
            "ml_model_id": current_model_id,
            "model_path": str(model_path),
        }

        # Обновляем runtime
        ML_RUNTIME_STATE["model_loaded"] = True
        if version:
            ML_RUNTIME_STATE["version"] = version
        if feature_order:
            ML_RUNTIME_STATE["feature_order"] = feature_order
            ML_RUNTIME_STATE["feature_count"] = len(feature_order)

        logger.info(f"Model loaded: {current_model_id}, features count: {len(feature_order)}")

        return {"model": cls._model, "meta": cls._meta}


    @classmethod
    def reload(cls):
        cls._model = None
        cls._meta = None
        cls._loaded_model_id = None
        return cls.load()