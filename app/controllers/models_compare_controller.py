# app/controllers/model_controller.py

import logging
from sqlalchemy.orm import Session

from app.services.registry_service import ModelRegistryService


class ModelsCompareController:

    def compare_models(self, model_a_id: int, model_b_id: int, db: Session) -> dict:
        registry = ModelRegistryService(db)

        model_a = registry.get_model(model_a_id)
        model_b = registry.get_model(model_b_id)

        if not model_a or not model_b:
            raise ValueError("One of models not found")

        comparison = {
            "model_a": {
                "id": model_a.id,
                "version": model_a.version,
                "is_active": model_a.is_active,
                "metrics": model_a.metrics,
                "features_count": len(model_a.features or []),
            },
            "model_b": {
                "id": model_b.id,
                "version": model_b.version,
                "is_active": model_b.is_active,
                "metrics": model_b.metrics,
                "features_count": len(model_b.features or []),
            },
            "diff": {
                "metric_diff": self._compare_metrics(model_a.metrics or {}, model_b.metrics or {}),
                "features_diff": self._compare_features(model_a.features, model_b.features),
            }
        }

        return comparison


    def _compare_metrics(self, m1: dict, m2: dict) -> dict:
        result = {}

        if not m1 or not m2:
            return result

        keys = set(m1.keys()).intersection(set(m2.keys()))

        for k in keys:
            result[k] = m2[k] - m1[k]

        return result


    def _compare_features(self, f1, f2) -> dict:
        f1 = set(f1 or [])
        f2 = set(f2 or [])

        return {
            "only_in_a": list(f1 - f2),
            "only_in_b": list(f2 - f1),
            "common": list(f1 & f2),
        }