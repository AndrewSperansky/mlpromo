# app/controllers/dataset_delete_controller.py

import logging
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from fastapi import HTTPException

from models.industrial_dataset import IndustrialDatasetRaw
from models.dataset_upload_history import DatasetUploadHistory

logger = logging.getLogger("promo_ml")


class DatasetDeleteController:
    """Контроллер для удаления батчей датасета"""

    def __init__(self, db: Session):
        self.db = db

    def delete_batch(self, batch_id: UUID, force: bool = False) -> dict:
        """
        Удаляет все записи, загруженные в рамках указанного batch_id.
        Если строк в данных нет — удаляет только запись из истории.
        """
        batch_id_str = str(batch_id)

        # ========== 1. ПРОВЕРЯЕМ СУЩЕСТВОВАНИЕ BATCH В ИСТОРИИ ==========
        upload_record = self.db.query(DatasetUploadHistory).filter(
            cast(DatasetUploadHistory.batch_id, String) == batch_id_str
        ).first()

        if not upload_record:
            raise HTTPException(status_code=404, detail="Batch not found in history")

        # ========== 2. УДАЛЯЕМ СТРОКИ ИЗ ДАННЫХ (если есть) ==========
        rows_deleted = 0
        try:
            rows_deleted = self.db.query(IndustrialDatasetRaw).filter(
                cast(IndustrialDatasetRaw.batch_id, String) == batch_id_str
            ).delete(synchronize_session=False)

            # Удаляем запись из истории загрузок
            self.db.delete(upload_record)
            self.db.commit()

            logger.info(
                f"🗑️ Deleted batch {batch_id_str}: {rows_deleted} rows removed from data, history record deleted")

            return {
                "status": "success",
                "batch_id": batch_id_str,
                "rows_deleted": rows_deleted,
                "force": force,
                "message": f"Deleted batch {batch_id_str} ({rows_deleted} rows)"
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error deleting batch {batch_id_str}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(e)}"
            )