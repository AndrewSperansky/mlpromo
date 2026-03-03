# app/services/dataset_service.py

from app.db.session import SessionLocal
from models.dataset_version import DatasetVersion


class DatasetService:

    def list_versions(self):
        db = SessionLocal()
        try:
            return (
                db.query(DatasetVersion)
                .order_by(DatasetVersion.created_at.desc())
                .all()
            )
        finally:
            db.close()