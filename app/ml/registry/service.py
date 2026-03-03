# app/ml/registry/service.py

from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_
from uuid import UUID

from models.ml_model import MLModel


class ModelRegistryService:

    def __init__(self, db: Session):
        self.db = db

    # =========================================
    # REGISTER MODEL
    # =========================================
    def register_model(
        self,
        *,
        name: str,
        version: str,
        algorithm: str,
        model_type: str,
        target: str,
        features: list[str],
        metrics: dict | None,
        model_path: Path,
        dataset_version_id: UUID,
        trained_rows_count: int,
    ) -> MLModel:

        stmt = select(MLModel).where(
            and_(
                MLModel.name == name,
                MLModel.version == version,
                MLModel.is_deleted.is_(False),
            )
        )

        existing = self.db.execute(stmt).scalar_one_or_none()

        if existing:
            return existing

        model = MLModel(
            name=name,
            version=version,
            algorithm=algorithm,
            model_type=model_type,
            target=target,
            features=features,
            metrics=metrics,
            model_path=str(model_path),
            is_active=False,
            trained_at=datetime.now(timezone.utc),
            dataset_version_id=dataset_version_id,
            trained_rows_count=trained_rows_count,
        )

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        return model

    # =========================================
    # PROMOTE MODEL
    # =========================================

    def promote_model(self, model_id: int) -> MLModel:

        stmt = select(MLModel).where(
            and_(
                MLModel.id == model_id,
                MLModel.is_deleted.is_(False),
            )
        )

        model = self.db.execute(stmt).scalar_one_or_none()

        if model is None:
            raise ValueError("Model not found")

        # deactivate all versions of same logical model
        self.db.execute(
            update(MLModel)
            .where(
                and_(
                    MLModel.name == model.name,
                    MLModel.is_deleted.is_(False),
                )
            )
            .values(is_active=False)
        )

        model.is_active = True

        self.db.commit()
        self.db.refresh(model)

        return model

    # =========================================
    # GET ACTIVE MODEL
    # =========================================
    def get_active_model(self, name: str) -> MLModel | None:

        stmt = select(MLModel).where(
            and_(
                MLModel.name == name,
                MLModel.is_active.is_(True),
                MLModel.is_deleted.is_(False),
            )
        )

        return self.db.execute(stmt).scalar_one_or_none()

    # =========================================
    # LIST MODEL
    # =========================================

    def list_models(self):
        return (
            self.db.query(MLModel)
            .filter(MLModel.is_deleted == False)
            .order_by(MLModel.created_at.desc())
            .all()
        )



    # =========================================
    # DEACTIVATE MODEL
    # =========================================

    def deactivate_model(self, model_id: int) -> MLModel:

        stmt = select(MLModel).where(
            and_(
                MLModel.id == model_id,
                MLModel.is_deleted.is_(False),
            )
        )

        model = self.db.execute(stmt).scalar_one_or_none()

        if model is None:
            raise ValueError("Model not found")

        model.is_active = False

        self.db.commit()
        self.db.refresh(model)

        return model


