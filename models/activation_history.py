# models/activation_history.py

from sqlalchemy import Column, BigInteger, Integer, DateTime, String, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class ModelActivationHistory(Base):
    __tablename__ = "model_activation_history"

    id = Column(BigInteger, primary_key=True)
    model_id = Column(Integer, ForeignKey("ml_model.id"), nullable=False)
    activated_at = Column(DateTime(timezone=True), server_default=func.now())
    activated_by = Column(String(50), nullable=True)