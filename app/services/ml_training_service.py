# app/services/ml_training_service.py

"""
ML Training Service — обучение на едином потоковом датасете.
"""

from typing import Dict, Any, Optional
import logging

from app.ml.train.train_pipeline import train_pipeline
from app.db.session import SessionLocal
from models.dataset_upload_history import DatasetUploadHistory
from models.industrial_dataset import IndustrialDatasetRaw

logger = logging.getLogger("promo_ml")


class MLTrainingService:

    def train(
            self,
            promote: bool = False,
            trigger: str = "manual",
    ) -> Dict[str, Any]:
        """
        Запускает обучение на ВСЁМ датасете из industrial_dataset_raw.
        Модель предсказывает k_uplift (коэффициент прироста).
        """
        logger.info(
            "🚀 ML training started",
            extra={
                "promote": promote,
                "trigger": trigger,
            }
        )

        db = SessionLocal()
        try:
            total_rows = db.query(IndustrialDatasetRaw).count()
            logger.info(f"📊 Total rows in dataset: {total_rows}")
        finally:
            db.close()

        if total_rows == 0:
            raise ValueError("No data in industrial_dataset_raw")

        # 🔥 Убираем target_column — train_pipeline сам знает целевую переменную
        result = train_pipeline(
            promote=promote,
            trigger=trigger,
        )

        logger.info(
            "✅ ML training completed",
            extra={
                "model_id": result.get("model_id"),
                "promoted": result.get("promoted"),
                "total_rows": total_rows,
            },
        )

        return {
            "status": "success",
            "model_id": result.get("model_id", 0),
            "model_name": result.get("model_name", "promo_uplift"),
            "total_rows": total_rows,
            "rows_removed": result.get("rows_removed", 0),
            "metrics": result.get("metrics", {}),
            "promoted": result.get("promoted", False),
            "stage": result.get("stage", "completed"),
            "note": result.get("note", f"Trained on {total_rows} rows, target: k_uplift")
        }

    def get_dataset_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику по датасету.
        """
        db = SessionLocal()
        try:
            total_rows = db.query(IndustrialDatasetRaw).count()

            last_upload = db.query(DatasetUploadHistory).order_by(
                DatasetUploadHistory.uploaded_at.desc()
            ).first()

            recent_uploads = db.query(DatasetUploadHistory).order_by(
                DatasetUploadHistory.uploaded_at.desc()
            ).limit(5).all()

            return {
                "total_rows": total_rows,
                "last_upload_at": last_upload.uploaded_at if last_upload else None,
                "last_upload_records": last_upload.records_added if last_upload else 0,
                "total_uploads": db.query(DatasetUploadHistory).count(),
                "recent_uploads": [
                    {
                        "batch_id": str(u.batch_id),
                        "uploaded_at": u.uploaded_at,
                        "records_added": u.records_added,
                        "total_after": u.total_records_after,
                        "duration_ms": u.duration_ms,
                        "status": u.status,
                    }
                    for u in recent_uploads
                ]
            }
        finally:
            db.close()