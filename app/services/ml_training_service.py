# app/services/ml_training_service.py

"""
ML Training Service — orchestration layer над train_pipeline.
Industrial version (dataset-version based).
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from models.ml_model import MLModel
import logging

from app.ml.train.train_pipeline import train_pipeline
from app.db.session import SessionLocal
from models.dataset_version import DatasetVersion
from sqlalchemy import text, select, delete, and_

logger = logging.getLogger("promo_ml")


class MLTrainingService:
    """
    Сервис обучения ML модели.

    Теперь НЕ обучает модель напрямую.
    Делегирует train_pipeline().
    Поддерживает обучение как на одном, так и на всех датасетах.
    """

    def train(
        self,
        dataset_version_id: Optional[UUID] = None,
        train_on_all: bool = False,
        promote: bool = False,
        trigger: str = "manual",
    ) -> Dict[str, Any]:
        """
        Запускает industrial pipeline обучения.

        Args:
            dataset_version_id (UUID, optional): Версия датасета (если train_on_all=False).
            train_on_all (bool): Флаг обучения на всех датасетах.
            promote (bool): Выполнять ли metrics-gated promotion.
            trigger (str): Источник запуска (api/manual/auto).

        Returns:
            dict: Результат обучения.
        """

        if train_on_all:
            return self.train_on_all_datasets(promote=promote, trigger=trigger)
        else:
            if not dataset_version_id:
                raise ValueError("dataset_version_id required when train_on_all=False")

            logger.info(
                "ML training started on single dataset",
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
                "ML training completed on single dataset",
                extra={
                    "model_id": result.get("model_id"),
                    "promoted": result.get("promoted"),
                    "stage": result.get("stage"),
                },
            )

            return result

    # app/services/ml_training_service.py

    def train_on_all_datasets(
            self,
            promote: bool = False,
            trigger: str = "api",
    ) -> Dict[str, Any]:
        """
        Обучает модель на всех доступных датасетах.
        """
        db = SessionLocal()
        try:
            # Получаем все READY датасеты
            datasets = db.query(DatasetVersion).filter(
                DatasetVersion.status == "READY"
            ).all()

            if not datasets:
                raise ValueError("No READY datasets found")

            logger.info(
                "ML training started on ALL datasets",
                extra={
                    "datasets_count": len(datasets),
                    "datasets": [str(ds.id) for ds in datasets],
                    "promote": promote,
                    "trigger": trigger,
                },
            )

            results = []
            for ds in datasets:
                try:
                    logger.info(f"Training on dataset {ds.id}")
                    result = train_pipeline(
                        dataset_version_id=ds.id,
                        promote=False,
                        trigger=f"{trigger}_part_of_all",
                    )

                    # ✅ ПОЛУЧАЕМ ID МОДЕЛИ ИЗ БД
                    model_name = result.get("model_name")
                    model_version = result.get("version")

                    # Ищем модель в БД по имени и версии
                    model_in_db = db.query(MLModel).filter(
                        and_(
                            MLModel.name == model_name,
                            MLModel.version == model_version,
                            MLModel.is_deleted == False
                        )
                    ).first()

                    if model_in_db:
                        # ✅ Подменяем строковый ID на числовой из БД
                        result["model_id"] = model_in_db.id
                        logger.info(f"Found model in DB with id={model_in_db.id}")
                    else:
                        logger.warning(f"Model not found in DB: {model_name}:{model_version}")
                        result["model_id"] = 0

                    results.append(result)
                    logger.info(f"Training on dataset {ds.id} completed, model_id={result.get('model_id')}")

                except Exception as e:
                    logger.error(f"Failed to train on dataset {ds.id}: {e}")
                    continue

            if not results:
                raise ValueError("No datasets could be trained successfully")

            # Выбираем лучшую модель
            best_model = min(results, key=lambda x: x.get("metrics", {}).get("rmse", float("inf")))

            # ✅ ФОРМИРУЕМ ПРАВИЛЬНУЮ СТРУКТУРУ
            final_result = {
                "status": "success",
                "model_id": best_model.get("model_id", 0),  # ← теперь число!
                "model_name": best_model.get("model_name", "unknown_model"),
                "datasets_used": [str(ds.id) for ds in datasets],
                "total_rows": sum(r.get("rows", 0) for r in results),
                "metrics": best_model.get("metrics", {}),
                "promoted": promote,
                "stage": "all_datasets_trained",
                "note": "Trained on each dataset separately, selected best model"
            }

            # Если promote=True, промотим лучшую модель
            if promote and final_result["model_id"]:
                from app.ml.registry.service import ModelRegistryService
                reg_db = SessionLocal()
                try:
                    registry = ModelRegistryService(reg_db)
                    registry.promote_model(final_result["model_id"])
                    final_result["promoted"] = True
                finally:
                    reg_db.close()

            logger.info(
                "ML training on ALL datasets completed",
                extra={
                    "total_datasets": len(datasets),
                    "successful": len(results),
                    "best_model_id": final_result["model_id"],
                },
            )

            return final_result

        finally:
            db.close()