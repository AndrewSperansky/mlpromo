# models/dataset_version.py


from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    row_count = Column(Integer, nullable=False)
    target_column = Column(String, nullable=False, default="SalesQty_Promo")
    status = Column(String, nullable=False, default="READY")  # READY | TRAINED | FAILED
    comment = Column(Text, nullable=True)