# app/controllers/model_delete_controller.py

import logging
import shutil
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.ml_model import MLModel
from app.models.activation_history import ModelActivationHistory
from app.services.activity_service import ActivityService
from app.models.user import User
from app.core.settings import settings

logger = logging.getLogger("promo_ml")


class ModelDeleteController:
    """Контроллер для удаления моделей"""

    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def delete_model(self, model_id: int) -> dict:
        """Полностью удаляет модель из БД и файловой системы."""
        model = self.db.get(MLModel, model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        if model.is_active:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete active model. Deactivate it first."
            )

        # ===== 1. УДАЛЯЕМ ФАЙЛЫ =====
        file_deletion_errors = []

        # Удаляем из candidate (если есть)
        candidate_path = Path(settings.ML_CANDIDATE_DIR) / f"{model.id}.cbm"
        if candidate_path.exists():
            try:
                candidate_path.unlink()
                logger.info(f"Deleted from candidate: {candidate_path}")

                # Удаляем соответствующий .meta.json
                meta_file = candidate_path.with_suffix('.meta.json')
                if meta_file.exists():
                    meta_file.unlink()
                    logger.info(f"Deleted meta from candidate: {meta_file}")
            except Exception as e:
                file_deletion_errors.append(str(e))
                logger.warning(f"Could not delete candidate files: {e}")

        # Удаляем из archive (всю папку, содержащую модель)
        archive_dir = Path(settings.ML_ARCHIVE_DIR)
        try:
            for f in archive_dir.glob(f"**/{model.id}.cbm"):
                model_folder = f.parent
                shutil.rmtree(model_folder)
                logger.info(f"Deleted archive folder: {model_folder}")
                break
        except Exception as e:
            file_deletion_errors.append(str(e))
            logger.warning(f"Could not delete archive folder: {e}")

        # ===== 2. УДАЛЯЕМ ИСТОРИЮ АКТИВАЦИЙ =====
        # 🔥 Исправлено: используем .__eq__() или просто == (SQLAlchemy понимает)
        try:
            self.db.query(ModelActivationHistory).filter(
                ModelActivationHistory.model_id == model_id  # type: ignore
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

        # Логируем действие
        ActivityService.log(
            db=self.db,
            user_id=self.current_user.id,
            action="delete_model",
            resource=f"model_{model_id}",
            details=f"Model {model_id} deleted by {self.current_user.username}"
        )

        message = "Model removed from database and filesystem"
        if file_deletion_errors:
            message += f". Note: {', '.join(file_deletion_errors)}"

        return {
            "status": "deleted",
            "model_id": model_id,
            "message": message
        }