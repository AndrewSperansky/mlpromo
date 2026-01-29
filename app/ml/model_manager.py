# app/ml/model_manager.py
import json
import asyncio
import logging
from pathlib import Path
from catboost import CatBoostRegressor

from app.ml.runtime_state import ML_RUNTIME_STATE
from app.ml.utils import sha256_file

logger = logging.getLogger("promo_ml")


class ModelManager:
    def __init__(self, model_path: str, check_interval: int = 5):
        self.model_path = Path(model_path)
        self.meta_path = self.model_path.with_suffix(".meta.json")
        self.check_interval = check_interval

        self.model = None
        self.meta = None


    @staticmethod
    def _update_state_on_error(self, error_msg: str):
        """Обновляет ML_RUNTIME_STATE при ошибке загрузки."""
        ML_RUNTIME_STATE.update({
            "model_loaded": False,
            "ml_model_id": None,
            "version": None,
            "feature_order": None,
            "checksum_verified": False,
            "status": "error",
            "errors": [error_msg],
            "warnings": [],
        })


    def load(self):
        # ---- load model ----
        if not self.model_path.exists():
            raise FileNotFoundError(self.model_path)

        model = CatBoostRegressor()
        model.load_model(str(self.model_path))

        # ---- load meta ----
        if not self.meta_path.exists():
            raise RuntimeError("model.meta.json is missing")

        with open(self.meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        # ---- checksum validation ----
        try:
            checksum_actual = sha256_file(self.model_path).lower()  # переводим checksum в нижний период
        except Exception as e:
            error_msg = f"Failed to calculate checksum: {e}"
            logger.error(error_msg)
            self._update_state_on_error(error_msg)
            raise

        checksum_expected = (
            meta.get("artifact", {})
            .get("model_checksum")
        )

        if checksum_expected:
            checksum_expected = checksum_expected.lower()

        logger.info(f"Read model_checksum from meta: {checksum_expected}")
        logger.info(f"Calculated checksum: {checksum_actual}")

        warnings = []
        status = "ok"
        checksum_verified = True

        if checksum_expected:
            if checksum_actual != checksum_expected:
                warnings.append("Model checksum mismatch")
                status = "degraded"
                checksum_verified = False
        else:
            warnings.append("Model checksum not provided in meta")
            checksum_verified = False

        # Файл модели не найден python

        if not self.model_path.exists():
            error_msg = f"Model file not found: {self.model_path.absolute()}"
            logger.error(error_msg)
            self._update_state_on_error(error_msg)  # ← ВЫЗОВ
            raise FileNotFoundError(error_msg)

        # Файл метаданных не найден python

        if not self.meta_path.exists():
            error_msg = f"Meta file not found: {self.meta_path.absolute()}"
            logger.error(error_msg)
            self._update_state_on_error(error_msg)  # ← ВЫЗОВ
            raise RuntimeError(error_msg)


        # Ошибка чтения JSON - метаданных python

        try:
            with open(self.meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in meta file: {e}"
            logger.error(error_msg)
            self._update_state_on_error(error_msg)  # ← ВЫЗОВ
            raise
        except Exception as e:
            error_msg = f"Failed to read meta file: {e}"
            logger.error(error_msg)
            self._update_state_on_error(error_msg)  # ← ВЫЗОВ
            raise

        # Ошибка загрузки модели CatBoost

        try:
            model = CatBoostRegressor()
            model.load_model(str(self.model_path))
        except Exception as e:
            error_msg = f"Failed to load CatBoost model: {e}"
            logger.error(error_msg)
            self._update_state_on_error(error_msg)  # ← ВЫЗОВ
            raise


        # ---- update runtime state ----
        ML_RUNTIME_STATE.update({
            "model_loaded": True,
            "ml_model_id": meta.get("ml_model_id"),
            "version": meta.get("version"),
            "feature_order": meta.get("feature_order"),
            "checksum_verified": checksum_verified,
            "status": status,
            "warnings": warnings,
            "errors": [],  # Очищаем ошибки при успешной загрузке
        })

        self.model = model
        self.meta = meta

        logger.info(
            "ML model loaded",
            extra={
                "ml_model_id": ML_RUNTIME_STATE.get("ml_model_id"),
                "version": ML_RUNTIME_STATE.get("version"),
                "checksum_verified": checksum_verified,
                "warnings": warnings,
            }
        )



    async def watch(self):
        while True:
            try:
                self.load()  # Можно добавить проверку изменений (Stage3)
                logger.info("Model reloaded by watcher")
            except Exception as e:
                logger.error("Watcher failed to reload model", extra={"error": str(e)})
            await asyncio.sleep(self.check_interval)
