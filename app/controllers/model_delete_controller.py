# app/controllers/model_delete_controller.py

import logging
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.ml_model import MLModel
from app.models.activation_history import ModelActivationHistory
from app.services.activity_service import ActivityService
from app.models.user import User

logger = logging.getLogger("promo_ml")


class ModelDeleteController:
    """Контроллер для удаления моделей"""

    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def delete_model(self, model_id: int) -> dict:
        """
        Полностью удаляет модель из БД и файловой системы.
        Даже если файлы отсутствуют, запись из БД удаляется.
        """
        # Находим модель
        model = self.db.get(MLModel, model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Если модель активна — ошибка (нельзя удалить активную)
        if model.is_active:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete active model. Deactivate it first."
            )

        # ===== 1. УДАЛЯЕМ ФАЙЛЫ (ИГНОРИРУЕМ ОШИБКИ) =====
        file_deletion_errors = []
        model_file = None

        if model.model_path:
            try:
                model_path_str = str(model.model_path)
                model_file = Path(model_path_str)

                # Удаляем файл модели
                if model_file.exists():
                    model_file.unlink()
                    logger.info(f"Deleted model file: {model_file}")
            except Exception as e:
                file_deletion_errors.append(f"Model file: {e}")
                logger.warning(f"Could not delete model file: {e}")

            # Удаляем meta.json (только если model_file определён)
            if model_file and model_file.exists():
                try:
                    meta_file = model_file.with_suffix('.meta.json')
                    if meta_file.exists():
                        meta_file.unlink()
                        logger.info(f"Deleted meta file: {meta_file}")
                except Exception as e:
                    file_deletion_errors.append(f"Meta file: {e}")
                    logger.warning(f"Could not delete meta file: {e}")

            # Удаляем shap-файлы (только если model_file определён)
            if model_file and model_file.exists():
                try:
                    model_dir = model_file.parent
                    for shap_file in model_dir.glob("shap_*"):
                        if shap_file.exists():
                            shap_file.unlink()
                            logger.info(f"Deleted shap file: {shap_file}")
                except Exception as e:
                    file_deletion_errors.append(f"Shap files: {e}")
                    logger.warning(f"Could not delete shap files: {e}")

        # ===== 2. УДАЛЯЕМ ИСТОРИЮ АКТИВАЦИЙ =====
        try:
            self.db.query(ModelActivationHistory).filter(
                ModelActivationHistory.model_id == model_id    # type: ignore
            ).delete(synchronize_session=False)
            logger.info(f"Deleted activation history for model {model_id}")
        except Exception as e:
            logger.warning(f"Could not delete activation history: {e}")

        # ===== 3. УДАЛЯЕМ ЗАПИСЬ ИЗ БД =====
        try:
            self.db.delete(model)
            self.db.commit()
            logger.info(f"Model {model_id} permanently deleted from database")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete model {model_id} from DB: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete model from database")

        # Формируем сообщение о результате
        message = "Model removed from database"
        if file_deletion_errors:
            message += f". Note: some files could not be deleted: {', '.join(file_deletion_errors)}"
        else:
            message += " and filesystem"

        # Логируем действие
        ActivityService.log(
            db=self.db,
            user_id=self.current_user.id,
            action="delete_model",
            resource=f"model_{model_id}",
            details=f"Model {model_id} deleted by {self.current_user.username}"
        )

        return {
            "status": "deleted",
            "model_id": model_id,
            "message": message
        }