from sqlalchemy import (
    Column, String, Integer, BigInteger, Float,
    DateTime, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.db.base import Base


class MLPredictionRequest(Base):
    __tablename__ = "ml_prediction_request"

    id = Column(UUID(as_uuid=True), primary_key=True)
    source = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)
    received_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class MLPredictionResult(Base):
    __tablename__ = "ml_prediction_result"

    id = Column(BigInteger, primary_key=True)
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ml_prediction_request.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_id = Column(
        Integer,
        ForeignKey("ml_model.id"),
        nullable=False,
    )
    model_version = Column(String, nullable=False)
    prediction_value = Column(Float, nullable=False)
    shap_values = Column(JSONB)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
