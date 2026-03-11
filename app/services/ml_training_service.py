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
from models.industrial_dataset import IndustrialDatasetRaw



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

    # ОБУЧЕНИЕ МОДЕЛИ СРАЗУ НА ВСЕХ ДАТАСЕТАХ

    def train_on_all_datasets(
            self,
            promote: bool = False,
            trigger: str = "api",
    ) -> Dict[str, Any]:
        """
        Обучает ОДНУ модель на ВСЕХ доступных датасетах.
        Создаёт временный объединённый датасет.
        """
        db = SessionLocal()
        try:
            # Получаем все READY датасеты
            datasets = db.query(DatasetVersion).filter(
                DatasetVersion.status == "READY"
            ).all()

            if not datasets:
                raise ValueError("No READY datasets found")

            dataset_ids = [ds.id for ds in datasets]

            logger.info(
                "🚀 ML training started on ALL datasets (combined)",
                extra={
                    "datasets_count": len(datasets),
                    "datasets": [str(ds_id) for ds_id in dataset_ids],
                    "promote": promote,
                    "trigger": trigger,
                },
            )

            # ========== 1. ЗАГРУЖАЕМ ВСЕ ДАННЫЕ ==========


            all_rows = []
            rows_per_dataset = {}

            for ds_id in dataset_ids:
                rows = db.query(IndustrialDatasetRaw).filter(
                    IndustrialDatasetRaw.dataset_version_id == str(ds_id)
                ).all()

                rows_per_dataset[str(ds_id)] = len(rows)

                for row in rows:
                    row_dict = {}
                    # Преобразуем SQLAlchemy объект в словарь
                    for column in row.__table__.columns:
                        value = getattr(row, column.name)
                        # Не копируем id и dataset_version_id
                        if column.name not in ['id', 'dataset_version_id']:
                            row_dict[column.name] = value
                    all_rows.append(row_dict)

            if not all_rows:
                raise ValueError("No data found in any dataset")

            logger.info(
                "📊 Data loaded from datasets",
                extra={
                    "total_rows": len(all_rows),
                    "rows_per_dataset": rows_per_dataset
                }
            )

            # ========== 2. СОЗДАЁМ ВРЕМЕННЫЙ ДАТАСЕТ ==========
            import uuid
            from datetime import datetime

            temp_dataset_id = uuid.uuid4()
            temp_dataset = DatasetVersion(
                id=temp_dataset_id,
                row_count=len(all_rows),
                status="READY",
                created_at=datetime.now()
            )
            db.add(temp_dataset)
            db.flush()

            logger.info(f"📁 Created temporary dataset: {temp_dataset_id}")

            # ========== 3. СОХРАНЯЕМ ВСЕ СТРОКИ ==========
            batch_size = 1000
            for i in range(0, len(all_rows), batch_size):
                batch = all_rows[i:i + batch_size]
                for row_dict in batch:
                    db_row = IndustrialDatasetRaw(
                        dataset_version_id=temp_dataset_id,
                        **row_dict
                    )
                    db.add(db_row)

                db.flush()
                logger.info(f"💾 Saved batch {i // batch_size + 1}/{(len(all_rows) - 1) // batch_size + 1}")

            db.commit()
            logger.info(f"✅ Saved all {len(all_rows)} rows to temporary dataset")

            # ========== 4. ОБУЧАЕМ МОДЕЛЬ ==========
            from app.ml.train.train_pipeline import train_pipeline

            logger.info("🎓 Starting model training on combined data...")

            result = train_pipeline(
                dataset_version_id=temp_dataset_id,
                promote=promote,
                trigger=f"{trigger}_combined",
            )

            logger.info(f"✅ Training completed, model_id: {result.get('model_id')}")

            # ========== 5. ФОРМИРУЕМ ОТВЕТ ==========
            final_result = {
                "status": "success",
                "model_id": result.get("model_id", 0),
                "model_name": result.get("model_name", "promo_uplift"),
                "datasets_used": [str(ds_id) for ds_id in dataset_ids],
                "rows_per_dataset": rows_per_dataset,
                "total_rows": len(all_rows),
                "metrics": result.get("metrics", {}),
                "promoted": result.get("promoted", False),
                "stage": "all_datasets_combined",
                "temporary_dataset_id": str(temp_dataset_id),
                "note": "✅ Trained on combined data from all datasets"
            }

            logger.info(
                "🎉 ML training on ALL datasets completed",
                extra={
                    "total_rows": len(all_rows),
                    "model_id": final_result["model_id"],
                    "metrics": final_result["metrics"],
                },
            )

            return final_result

        except Exception as e:
            logger.error(f"❌ Error in combined training: {e}", exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()

    def cleanup_temp_datasets(self, hours: int = 24):
        """
        Удаляет временные датасеты старше N часов.
        """
        from datetime import datetime, timedelta
        from sqlalchemy import and_

        db = SessionLocal()
        try:
            cutoff = datetime.now() - timedelta(hours=hours)

            # Находим старые датасеты с пометкой temporary
            temp_datasets = db.query(DatasetVersion).filter(
                and_(
                    DatasetVersion.status == "READY",
                    DatasetVersion.created_at < cutoff,
                    DatasetVersion.id.in_(
                        text(
                            "SELECT dataset_version_id FROM industrial_dataset_raw WHERE dataset_version_id IS NOT NULL")
                    )
                )
            ).all()

            for ds in temp_datasets:
                logger.info(f"🧹 Cleaning up temporary dataset: {ds.id}")
                # Удаляем связанные строки
                db.execute(
                    text("DELETE FROM industrial_dataset_raw WHERE dataset_version_id = :ds_id"),
                    {"ds_id": ds.id}
                )
                # Удаляем сам датасет
                db.delete(ds)

            db.commit()
            logger.info(f"🧹 Cleaned up {len(temp_datasets)} temporary datasets")

        finally:
            db.close()