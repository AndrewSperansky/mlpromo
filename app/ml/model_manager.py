# app/ml/model_manager.py

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.ml.runtime_state import ML_RUNTIME_STATE
from app.ml.model_loader import ModelLoader
from app.core.settings import settings

logger = logging.getLogger("promo_ml")


class ModelManager:
    """
    Управляет жизненным циклом ML-модели.
    Загружает модель и метаданные о фичах.
    """

    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self._current_model_id: Optional[int] = None
        self._current_feature_order: List[str] = []

    def load(self) -> bool:
        """
        Загружает модель через ModelLoader.
        Обновляет runtime state.

        Returns:
            bool: True если модель загружена успешно, иначе False
        """
        try:
            result = ModelLoader.load()
            model = result.get("model")
            meta = result.get("meta", {})

            if model is None:
                logger.error("ModelLoader returned None")
                self._set_error_state("ModelLoader returned None")
                return False

            # Получаем список фич из метаданных
            feature_order = meta.get("feature_order", [])
            if not feature_order:
                logger.warning("No feature_order in model metadata, using empty list")
                feature_order = []

            # Обновляем runtime state
            ML_RUNTIME_STATE.update({
                "model_loaded": True,
                "ml_model_id": meta.get("ml_model_id") or ML_RUNTIME_STATE.get("ml_model_id"),
                "version": meta.get("version"),
                "feature_order": feature_order,
                "feature_count": len(feature_order),
                "status": "ok",
                "errors": [],
                "model_path": meta.get("model_path") or ML_RUNTIME_STATE.get("model_path"),
            })

            self._current_model_id = ML_RUNTIME_STATE.get("ml_model_id")
            self._current_feature_order = feature_order

            logger.info(
                f"✅ ML model loaded successfully",
                extra={
                    "ml_model_id": self._current_model_id,
                    "version": ML_RUNTIME_STATE.get("version"),
                    "feature_count": len(feature_order),
                    "model_path": ML_RUNTIME_STATE.get("model_path"),
                }
            )

            return True

        except FileNotFoundError as e:
            logger.warning(f"Model file not found: {e}")
            self._set_error_state(f"Model file not found: {e}")
            return False

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse model metadata: {e}")
            self._set_error_state(f"Invalid metadata: {e}")
            return False

        except Exception as e:
            logger.exception("ModelManager failed to load model")
            self._set_error_state(str(e))
            return False

    def reload(self) -> bool:
        """
        Принудительно перезагружает модель.

        Returns:
            bool: True если перезагрузка успешна
        """
        logger.info("Forcing model reload")
        # Очищаем кэш в ModelLoader
        from app.ml.model_loader import ModelLoader
        ModelLoader.reload()
        return self.load()

    def get_feature_order(self) -> List[str]:
        """Возвращает порядок фич, ожидаемых моделью"""
        return self._current_feature_order

    def get_model_info(self) -> Dict[str, Any]:
        """Возвращает информацию о текущей модели"""
        return {
            "model_id": self._current_model_id,
            "feature_count": len(self._current_feature_order),
            "features": self._current_feature_order[:10],  # первые 10 для отладки
            "is_loaded": ML_RUNTIME_STATE.get("model_loaded", False),
            "version": ML_RUNTIME_STATE.get("version"),
            "status": ML_RUNTIME_STATE.get("status"),
        }

    def validate_features(self, features: Dict[str, Any]) -> bool:
        """
        Проверяет, что все необходимые фичи присутствуют.

        Args:
            features: Словарь с фичами

        Returns:
            bool: True если все фичи есть, иначе False
        """
        if not self._current_feature_order:
            logger.warning("Feature order not set, skipping validation")
            return True

        missing = set(self._current_feature_order) - set(features.keys())
        if missing:
            logger.error(f"Missing features for model: {missing}")
            return False

        return True

    def _set_error_state(self, error_message: str) -> None:
        """Устанавливает состояние ошибки в runtime state"""
        ML_RUNTIME_STATE.update({
            "model_loaded": False,
            "status": "error",
            "errors": ML_RUNTIME_STATE.get("errors", []) + [error_message],
        })

    async def watch(self) -> None:
        """
        Watcher: периодически проверяет и перезагружает модель.
        """
        logger.info(f"ModelManager watcher started (interval: {self.check_interval}s)")

        while True:
            try:
                await asyncio.sleep(self.check_interval)

                # Проверяем, нужно ли перезагрузить модель
                current_model_id = ML_RUNTIME_STATE.get("ml_model_id")

                if current_model_id != self._current_model_id:
                    logger.info(
                        f"Model ID changed from {self._current_model_id} to {current_model_id}, reloading"
                    )
                    self.reload()
                else:
                    # Периодическая проверка целостности
                    if not ML_RUNTIME_STATE.get("model_loaded", False):
                        logger.warning("Model not loaded, attempting reload")
                        self.load()
                    else:
                        logger.debug("Model is healthy, no reload needed")

            except asyncio.CancelledError:
                logger.info("ModelManager watcher cancelled")
                break
            except Exception as e:
                logger.error(f"Error in watcher: {e}")
                continue