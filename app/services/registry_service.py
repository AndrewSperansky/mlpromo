# app/services/registry_service.py

import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

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
        model_path: Optional[Path] = None,  # ← опциональный
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
            model_path=str(model_path) if model_path else None,  # ← может быть None
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

        # ===== ПЕРЕМЕЩАЕМ ФАЙЛЫ =====

        MODELS_DIR = Path("/app/models")
        current_dir = MODELS_DIR / "current"
        candidate_dir = MODELS_DIR / "_candidate"
        archive_dir = MODELS_DIR / "archive"

        # Создаём папки если нет
        current_dir.mkdir(exist_ok=True)
        archive_dir.mkdir(exist_ok=True)

        # Если модель в _candidate — перемещаем в current
        if model.model_path and "_candidate" in model.model_path:
            old_path = Path(model.model_path)

            # Новый путь в current
            new_path = current_dir / old_path.name

            # Копируем файл модели
            shutil.copy(old_path, new_path)

            # Копируем meta.json если есть
            meta_old = old_path.with_suffix('.meta.json')
            if meta_old.exists():
                shutil.copy(meta_old, current_dir / meta_old.name)

            # Копируем shap-файлы
            for f in candidate_dir.glob("shap_*"):
                shutil.copy(f, current_dir / f.name)

            # Обновляем путь в БД
            model.model_path = str(new_path)

        # Если модель уже в current — архивируем старую
        elif model.model_path and "current" in model.model_path:
            # Здесь логика архивации...
            pass


        self.db.commit()
        self.db.refresh(model)

        return model

    # =========================================
    # GET ANY MODEL
    # =========================================
    def get_model(self, model_id: int) -> MLModel | None:

        model = select(MLModel).where(
            and_(
                MLModel.name == model_id,
                MLModel.is_deleted.is_(False),
            )
        )

        if not model:
            raise ValueError(f"Model {model_id} not found")

        return self.db.execute(model).scalar_one_or_none()



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


