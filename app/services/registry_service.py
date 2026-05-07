# app/services/registry_service.py

import logging
import shutil
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.ml_model import MLModel
from app.ml.model_registry.lineage import record_lineage_event
from app.core.settings import settings

logger = logging.getLogger("promo_ml")


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
            model_path: Optional[Path] = None,
            trained_rows_count: int,
    ) -> MLModel:
        """Регистрирует новую модель в БД."""
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
            model_path=str(model_path) if model_path else None,
            is_active=False,
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
        logger.info(f"🚀 Starting promotion process for model {model_id}")

        new_model = self.get_model(model_id)
        if new_model is None:
            raise ValueError(f"Model {model_id} not found")

        current_model = (
            self.db.query(MLModel)
            .filter(MLModel.is_active == True, MLModel.is_deleted == False)
            .first()
        )

        # Governance check
        if current_model is not None:
            if current_model.id == new_model.id:
                return new_model
            self.validate_promotion(current_model, new_model)  # type: ignore

        # Deactivate all active models
        self.db.query(MLModel).filter(MLModel.is_active == True).update({"is_active": False})

        # Activate new model
        new_model.is_active = True
        self.db.commit()
        self.db.refresh(new_model)

        # Record lineage
        record_lineage_event(
            event_type="promoted",
            model_id=str(model_id),
            reason="Model promoted to champion",
            metadata={
                "previous_model_id": current_model.id if current_model else None,
                "rmse": new_model.metrics.get("rmse") if new_model.metrics else None
            }
        )

        # Archive old current model (move to archive)
        self._archive_old_current_model()

        # Cleanup candidate models
        self._cleanup_candidate_models(keep_last=3)

        # Update meta in current directory
        self._update_current_meta(new_model)

        # Move model files
        self._move_model_files(new_model)

        return new_model

    def force_promote_model(self, model_id: int) -> MLModel:
        """Принудительная активация без проверки метрик"""
        new_model = self.get_model(model_id)
        if new_model is None:
            raise ValueError(f"Model {model_id} not found")

        self.db.query(MLModel).filter(MLModel.is_active == True).update({"is_active": False})
        new_model.is_active = True
        self.db.commit()

        # Archive old current model
        self._archive_old_current_model()

        # Cleanup candidate models
        self._cleanup_candidate_models(keep_last=3)

        return new_model

    # =========================================
    # CLEANUP METHODS
    # =========================================

    @staticmethod
    def _cleanup_candidate_models(keep_last: int = 3):
        """Оставляет только последние N моделей в candidate."""

        candidate_dir = Path(settings.ML_CANDIDATE_DIR)
        candidate_dir.mkdir(parents=True, exist_ok=True)

        if not candidate_dir.exists():
            return

        # Получаем все .cbm файлы с их временем модификации
        cbm_files = list(candidate_dir.glob("*.cbm"))
        if not cbm_files:
            return

        # Сортируем по времени (новые первые)
        cbm_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Определяем, какие модели оставляем (первые keep_last)
        to_keep = set(f.stem for f in cbm_files[:keep_last])
        to_delete = cbm_files[keep_last:]

        # Удаляем старые модели
        for old_cbm in to_delete:
            model_stem = old_cbm.stem

            # Удаляем .cbm
            old_cbm.unlink()
            logger.info(f"Deleted: {old_cbm.name}")

            # Удаляем соответствующий .meta.json
            meta_file = candidate_dir / f"{model_stem}.meta.json"
            if meta_file.exists():
                meta_file.unlink()
                logger.info(f"Deleted: {meta_file.name}")

            # Удаляем SHAP-файлы
            for shap_file in candidate_dir.glob(f"{model_stem}_shap*"):
                shap_file.unlink()
                logger.info(f"Deleted: {shap_file.name}")

        # Удаляем orphan meta.json (только если нет соответствующего .cbm среди оставшихся)
        # for meta_file in candidate_dir.glob("*.meta.json"):
        #     model_stem = meta_file.stem
        #     if model_stem not in to_keep:
        #         cbm_file = candidate_dir / f"{model_stem}.cbm"
        #         if not cbm_file.exists():
        #             meta_file.unlink()
        #             logger.info(f"Deleted orphan meta: {meta_file.name}")

        # Очищаем общие shap-файлы (если нет моделей)
        if not cbm_files:
            for shap_file in candidate_dir.glob("shap_*"):
                shap_file.unlink()
            metrics_file = candidate_dir / "training_metrics.json"
            if metrics_file.exists():
                metrics_file.unlink()
                logger.info("Deleted: training_metrics.json")

        logger.info(f"✅ candidate cleanup completed, kept {len(to_keep)} models")



    def _archive_old_current_model(self):
        """
        Перемещает старые модели из current в archive.
        Создаёт поддиректорию с timestamp.
        """
        from pathlib import Path
        import shutil
        from datetime import datetime


        current_dir = Path(settings.ML_CURRENT_DIR)
        archive_dir = Path(settings.ML_ARCHIVE_DIR)

        current_dir.mkdir(parents=True, exist_ok=True)
        archive_dir.mkdir(parents=True, exist_ok=True)


        logger.info(f"📁 current_dir: {current_dir}")
        logger.info(f"📁 archive_dir: {archive_dir}")


        # Находим активную модель в БД
        active_model = (
            self.db.query(MLModel)
            .filter(MLModel.is_active == True, MLModel.is_deleted == False)
            .first()
        )

        if not active_model:
            logger.info("No active model found, skipping archive")
            return

        # Создаём архивную директорию с timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = archive_dir / f"archive_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        moved_count = 0
        for f in current_dir.glob("*"):
            if f.is_file():
                # Не архивируем файлы активной модели
                active_model_path = str(active_model.model_path) if active_model.model_path else None
                if active_model_path and active_model_path in str(f):
                    continue
                # Не архивируем текущий meta.json активной модели
                if f.name == "cb_promo_v1.meta.json" and active_model.model_path:
                    continue

                try:
                    shutil.move(str(f), str(backup_dir / f.name))
                    moved_count += 1
                    logger.info(f"  Archived: {f.name} -> {backup_dir.name}")
                except Exception as e:
                    logger.warning(f"  Failed to archive {f.name}: {e}")

        if moved_count > 0:
            logger.info(f"✅ Archived {moved_count} files to {backup_dir}")
        else:
            # Если нечего архивировать — удаляем пустую директорию
            try:
                backup_dir.rmdir()
            except:
                pass

    # =========================================
    # HELPER METHODS
    # =========================================

    def _update_current_meta(self, model: MLModel) -> None:
        """Обновляет meta.json в директории current"""
        try:
            from pathlib import Path
            current_dir = Path(settings.ML_CURRENT_DIR)
            current_dir.mkdir(parents=True, exist_ok=True)

            # 🔥 Правильный путь — по ID модели
            meta_path = current_dir / f"{model.id}.meta.json"

            # 🔥 Для обратной совместимости — создаём симлинк или копию как cb_promo_v1.meta.json
            legacy_path = current_dir / "cb_promo_v1.meta.json"

            if meta_path.exists():
                with open(meta_path, 'r') as f:
                    meta = json.load(f)

                if model.metrics and isinstance(model.metrics, dict):
                    conformal = model.metrics.get("conformal")
                    if conformal:
                        meta["conformal"] = conformal
                        meta["conformal_q_hat"] = conformal.get("q_hat")

                        # Сохраняем в основной файл
                        with open(meta_path, 'w') as f:
                            json.dump(meta, f, indent=2)

                        # Копируем в legacy файл для совместимости
                        import shutil
                        shutil.copy2(meta_path, legacy_path)

                        logger.info(f"✅ Updated meta.json: {meta_path} and {legacy_path}")
        except Exception as e:
            logger.warning(f"Failed to update meta.json: {e}")

    # =========================================
    # MOVE MODELS FILES
    # =========================================

    def _move_model_files(self, model: MLModel) -> None:
        """Перемещает файлы модели в папку current"""
        try:
            from pathlib import Path
            import shutil


            current_dir = Path(settings.ML_CURRENT_DIR)  # /app/models/current
            candidate_dir = Path(settings.ML_CANDIDATE_DIR)  # /app/models/candidate
            metrics_dir = Path(settings.ML_METRICS_DIR)  # /app/models/metrics


            logger.info(f"📁 current_dir: {current_dir}")
            logger.info(f"📁 candidate_dir: {candidate_dir}")
            logger.info(f"📁 metrics_dir: {metrics_dir}")

            current_dir.mkdir(parents=True, exist_ok=True)
            candidate_dir.mkdir(parents=True, exist_ok=True)
            metrics_dir.mkdir(parents=True, exist_ok=True)


            # 🔥 ВСЕГДА копируем SHAP-файлы при активации
            for f in candidate_dir.glob("shap_*"):
                shutil.copy2(str(f), str(current_dir / f.name))
                # .copy2 (копируем, оставляя в candidate для других моделей)
                logger.info(f"Copied shap: {f.name}")

            if model.model_path and "candidate" in model.model_path:
                old_path = Path(model.model_path)
                new_path = current_dir / old_path.name

                # 1. Копируем .cbm
                shutil.move(old_path, new_path)
                logger.info(f"Copied model: {old_path.name} -> {new_path}")

                # 2. Копируем .meta.json
                meta_old = old_path.with_suffix('.meta.json')
                if meta_old.exists():
                    shutil.move(meta_old, current_dir / meta_old.name)
                    logger.info(f"Copied meta: {meta_old.name}")

                # 3. Копируем SHAP-файлы
                # for f in candidate_dir.glob("shap_*"):
                #     shutil.copy2(str(f), str(current_dir / f.name))
                #     # .copy2 (копируем, оставляя в candidate для других моделей)
                #     logger.info(f"Copied shap: {f.name}")

                # 4. 🔥 Копируем training_metrics.json из metrics/ в current/
                # metrics_src = metrics_dir / "training_metrics.json"
                # if metrics_src.exists():
                #     shutil.move(metrics_src, current_dir / "training_metrics.json")
                #     logger.info(f"Copied training_metrics.json from {metrics_src}")

                # 5. Обновляем путь в БД
                model.model_path = str(new_path)
                self.db.commit()

                logger.info(f"✅ Model files moved to {current_dir}")
            else:
                logger.info(f"Model already in current directory: {model.model_path}")

        except Exception as e:
            logger.error(f"Failed to move model files: {e}")

    # =========================================
    # CRUD METHODS
    # =========================================

    def get_model(self, model_id: int) -> MLModel | None:
        stmt = select(MLModel).where(
            and_(
                MLModel.id == model_id,
                MLModel.is_deleted.is_(False),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_active_model(self, name: str) -> MLModel | None:
        stmt = select(MLModel).where(
            and_(
                MLModel.name == name,
                MLModel.is_active.is_(True),
                MLModel.is_deleted.is_(False),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()



    def get_active_model_by_algorithm(self, algorithm: str) -> Optional[MLModel]:
        """
        Возвращает активную модель с указанным алгоритмом.

        Args:
            algorithm: 'catboost', 'pytorch_lstm', 'pytorch_mlp'
        """
        stmt = select(MLModel).where(
            and_(
                MLModel.algorithm == algorithm,
                MLModel.is_active == True,
                MLModel.is_deleted == False,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()


    def get_active_models_by_type(self, model_type: str) -> List[MLModel]:
        """
        Возвращает список активных моделей указанного типа.

        Args:
            model_type: 'tabular', 'time_series'
        """
        stmt = select(MLModel).where(
            and_(
                MLModel.model_type == model_type,
                MLModel.is_active == True,
                MLModel.is_deleted == False,
            )
        )
        return self.db.execute(stmt).scalars().all()    # type: ignore



    def list_models(self):
        return (
            self.db.query(MLModel)
            .filter(MLModel.is_deleted == False)
            .order_by(MLModel.created_at.desc())
            .all()
        )

    def deactivate_model(self, model_id: int) -> MLModel:
        model = self.get_model(model_id)
        if model is None:
            raise ValueError("Model not found")
        model.is_active = False
        self.db.commit()
        self.db.refresh(model)
        logger.info(f"Model {model_id} deactivated")
        return model



    def validate_promotion(self, current_model: MLModel, new_model: MLModel) -> None:
        """Проверяет, можно ли продвигать новую модель."""
        current_metrics = current_model.metrics or {}
        new_metrics = new_model.metrics or {}

        if not current_metrics:
            raise ValueError(f"Current model {current_model.id} has no metrics")

        if not new_metrics:
            raise ValueError(f"New model {new_model.id} has no metrics")

        possible_metrics = ["rmse", "mae", "mape", "r2", "accuracy"]
        metric_name = None
        for m in possible_metrics:
            if m in current_metrics and m in new_metrics:
                metric_name = m
                break

        if not metric_name:
            raise ValueError(f"No common metrics found")

        lower_is_better_metrics = {"rmse", "mae", "mape"}
        current_value = current_metrics[metric_name]
        new_value = new_metrics[metric_name]

        if metric_name in lower_is_better_metrics:
            if new_value > current_value:
                raise ValueError(f"Promotion rejected: new model has worse {metric_name}")
        else:
            if new_value < current_value:
                raise ValueError(f"Promotion rejected: new model has worse {metric_name}")


