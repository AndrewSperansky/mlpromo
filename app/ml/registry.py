# app/ml/registry.py
import joblib
from sqlalchemy.orm import Session
from models.ml_model import MLModel
from typing import Any


def load_active_model(db: Session) -> tuple[Any, MLModel]:
    model_row: MLModel | None = (
        db.query(MLModel)
        .filter(
            MLModel.is_active == True,
            MLModel.is_deleted == False,
        )
        .one_or_none()
    )

    if model_row is None:
        raise RuntimeError("No active ML model found")

    model: Any = joblib.load(model_row.model_path)
    return model, model_row
