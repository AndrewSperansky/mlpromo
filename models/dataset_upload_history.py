# models/dataset_upload_history.py

from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from datetime import datetime


class DatasetUploadHistory(Base):
    __tablename__ = "dataset_upload_history"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(UUID(as_uuid=True), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.now)
    records_added = Column(Integer, nullable=False)
    total_records_after = Column(Integer, nullable=False)
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)