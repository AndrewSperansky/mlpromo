# app/services/ml_training_service.py

"""
ML Training Service — orchestration layer над train_pipeline.
Industrial version (dataset-version based).
"""

from typing import Dict, Any
from uuid import UUID
import logging

from app.ml.train.train_pipeline import train_pipeline

logger = logging.getLogger("promo_ml")


class MLTrainingService:
    """
    Сервис обучения ML модели.

    Теперь НЕ обучает модель напрямую.
    Делегирует train_pipeline().
    """

    def train(
        self,
        dataset_version_id: UUID,
        promote: bool = False,
        trigger: str = "manual",
    ) -> Dict[str, Any]:
        """
        Запускает industrial pipeline обучения.

        Args:
            dataset_version_id (UUID): Версия датасета.
            promote (bool): Выполнять ли metrics-gated promotion.
            trigger (str): Источник запуска (api/manual/auto).

        Returns:
            dict: Результат обучения.
        """

        logger.info(
            "ML training started",
            extra={
                "dataset_version_id": str(dataset_version_id),
                "promote": promote,
                "trigger": trigger,
            },
        )

        result = train_pipeline(
            dataset_version_id=dataset_version_id,
            promote=promote,
            trigger=trigger,
        )

        logger.info(
            "ML training completed",
            extra={
                "model_id": result.get("model_id"),
                "promoted": result.get("promoted"),
                "stage": result.get("stage"),
            },
        )

        return result