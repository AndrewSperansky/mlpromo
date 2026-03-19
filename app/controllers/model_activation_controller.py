# app/controllers/model_controller.py

import logging
from sqlalchemy.orm import Session

from app.services.registry_service import ModelRegistryService
from models.activation_history import ModelActivationHistory
from app.ml.runtime_state import ML_RUNTIME_STATE

logger = logging.getLogger(__name__)


class ModelActivationController:

    def promote_model(self, model_id: int, db: Session) -> dict:
        registry = ModelRegistryService(db)

        # 1. Promote (внутри уже commit)
        model = registry.promote_model(model_id)

        # 2. Обновляем runtime state
        ML_RUNTIME_STATE["ml_model_id"] = model.id
        ML_RUNTIME_STATE["version"] = model.version
        ML_RUNTIME_STATE["feature_order"] = list(model.features) if model.features else []
        ML_RUNTIME_STATE["model_path"] = model.model_path
        ML_RUNTIME_STATE["model_loaded"] = False

        # 3. Обновляем contract
        ML_RUNTIME_STATE["contract"]["model_path"] = model.model_path

        # 4. Audit (без commit)
        history_entry = ModelActivationHistory(
            model_id=model.id,
            activated_by="user"
        )
        db.add(history_entry)
        db.commit()

        logger.info(
            f"✅ Model {model_id} promoted. Features: {ML_RUNTIME_STATE['feature_order']}"
        )

        return {
            "status": "promoted",
            "model_id": model.id,
            "name": model.name,
            "version": model.version,
            "dataset_version_id": str(model.dataset_version_id),
        }