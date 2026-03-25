# app/services/dataset_service.py

from app.db.session import SessionLocal
from models.industrial_dataset import IndustrialDatasetRaw
from models.dataset_upload_history import DatasetUploadHistory


class DatasetService:

    def get_stats(self):
        """Возвращает статистику по единому датасету"""
        db = SessionLocal()
        try:
            total_rows = db.query(IndustrialDatasetRaw).count()

            # Последняя загрузка
            last_upload = db.query(DatasetUploadHistory).order_by(
                DatasetUploadHistory.uploaded_at.desc()
            ).first()

            # Все загрузки для истории
            uploads = db.query(DatasetUploadHistory).order_by(
                DatasetUploadHistory.uploaded_at.desc()
            ).limit(50).all()

            return {
                "total_rows": total_rows,
                "last_updated": last_upload.uploaded_at.isoformat() if last_upload else None,
                "last_upload_records": last_upload.records_added if last_upload else 0,
                "total_uploads": len(uploads),
                "upload_history": [
                    {
                        "id": h.id,
                        "batch_id": str(h.batch_id),
                        "uploaded_at": h.uploaded_at.isoformat(),
                        "records_added": h.records_added,
                        "total_records_after": h.total_records_after,
                        "status": h.status,
                        "error_message": h.error_message,
                        "duration_ms": h.duration_ms
                    }
                    for h in uploads
                ]
            }
        finally:
            db.close()