# app/api/v1/ml/models_endpoint.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from models.ml_model import MLModel

router = APIRouter(prefix="/ml", tags=["ml"])


@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    models = (
        db.query(MLModel)
        .filter(MLModel.is_deleted == False)
        .order_by(MLModel.created_at.desc())
        .all()
    )

    return [
        {
            "name": m.name,
            "algorithm": m.algorithm,
            "version": m.version,
            "is_active": m.is_active,
            "trained_at": m.trained_at,
            "features": m.features,
            "metrics": m.metrics,
        }
        for m in models
    ]
