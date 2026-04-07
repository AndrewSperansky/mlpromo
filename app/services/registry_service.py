# app/services/registry_service.py

import logging
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_
from uuid import UUID

from models.ml_model import MLModel
from app.core.settings import settings

logger = logging.getLogger(__name__)


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
        """
        Регистрирует новую модель в БД.

        """

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

        # 1. Получаем новую модель (кандидата)
        new_model = self.get_model(model_id)
        if new_model is None:
            logger.error(f"❌ Model {model_id} not found")
            raise ValueError(f"Model {model_id} not found")

        logger.info(f"📦 Candidate model: {new_model.name}:{new_model.version} (id={new_model.id})")
        logger.info(f"   Metrics: {new_model.metrics}")

        # 2. Получаем текущую активную модель (Champion)
        current_model: Optional[MLModel] = (
            self.db.query(MLModel)
            .filter(
                MLModel.is_active == True,
                MLModel.is_deleted == False
            )
            .first()
        )

        # 3. GOVERNANCE CHECK
        if current_model is not None:
            logger.info(f"🏆 Current champion: {current_model.name}:{current_model.version} (id={current_model.id})")
            logger.info(f"   Metrics: {current_model.metrics}")

            if current_model.id == new_model.id:
                logger.warning(f"⚠️ Model {model_id} is already active, skipping promotion")
                return new_model

            # Проверяем, можно ли продвигать
            try:
                self.validate_promotion(current_model, new_model)
                logger.info(f"✅ Promotion validation passed")
            except ValueError as e:
                logger.error(f"❌ Promotion rejected: {e}")
                raise
        else:
            logger.info("🎯 No active model found, this will be the first champion")

        # 4. Деактивируем ВСЕ активные модели
        deactivated = self.db.query(MLModel).filter(
            MLModel.is_active == True
        ).update({"is_active": False})

        if deactivated:
            logger.info(f"🔴 Deactivated {deactivated} existing model(s)")

        # 5. Активируем новую модель
        new_model.is_active = True
        self.db.commit()
        self.db.refresh(new_model)

        logger.info(f"🟢 Activated new champion: {new_model.name}:{new_model.version} (id={new_model.id})")

        # 6. После активации модели, обновляем meta.json в current директории
        self._update_current_meta(new_model)

        # 7. Перемещаем файлы
        self._move_model_files(new_model)

        return new_model


    def _update_current_meta(self, model: MLModel) -> None:
        """Обновляет meta.json в директории current"""
        try:
            import json
            from pathlib import Path

            models_dir = Path("/app/models")
            current_dir = models_dir / "current"
            meta_path = current_dir / "cb_promo_v1.meta.json"

            if meta_path.exists():
                with open(meta_path, 'r') as f:
                    meta = json.load(f)

                # Добавляем conformal данные из метрик модели
                if model.metrics and isinstance(model.metrics, dict):
                    conformal = model.metrics.get("conformal")
                    if conformal:
                        meta["conformal"] = conformal
                        meta["conformal_q_hat"] = conformal.get("q_hat")

                        with open(meta_path, 'w') as f:
                            json.dump(meta, f, indent=2)

                        logger.info(f"✅ Updated meta.json with conformal data: q_hat={conformal.get('q_hat')}")
        except Exception as e:
            logger.warning(f"Failed to update meta.json: {e}")



    def _move_model_files(self, model: MLModel) -> None:
        """Перемещает файлы модели в папку current"""
        try:
            MODELS_DIR = Path("/app/models")
            current_dir = MODELS_DIR / "current"
            candidate_dir = MODELS_DIR / "_candidate"
            archive_dir = MODELS_DIR / "archive"

            current_dir.mkdir(exist_ok=True)
            archive_dir.mkdir(exist_ok=True)

            if model.model_path and "_candidate" in model.model_path:
                old_path = Path(model.model_path)
                new_path = current_dir / old_path.name

                logger.info(f"📁 Moving model files from {old_path} to {new_path}")

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
                self.db.commit()

                logger.info(f"✅ Model files moved successfully")
            elif model.model_path and "current" in model.model_path:
                logger.info(f"📁 Model already in current directory, no move needed")

        except Exception as e:
            logger.error(f"❌ Failed to move model files: {e}")
            # Не прерываем процесс — модель уже активирована

    # =========================================
    # GET ANY MODEL
    # =========================================
    def get_model(self, model_id: int) -> MLModel | None:
        stmt = select(MLModel).where(
            and_(
                MLModel.id == model_id,
                MLModel.is_deleted.is_(False),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

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
        model = self.get_model(model_id)
        if model is None:
            raise ValueError("Model not found")

        model.is_active = False
        self.db.commit()
        self.db.refresh(model)

        logger.info(f"🔴 Model {model_id} deactivated")
        return model

    # =========================================
    # VALIDATE PROMOTION
    # =========================================
    def validate_promotion(self, current_model: MLModel, new_model: MLModel) -> None:
        """
        Проверяет, можно ли продвигать новую модель.
        Raises ValueError если новая модель хуже или равна текущей.
        """

        current_metrics = current_model.metrics or {}
        new_metrics = new_model.metrics or {}

        logger.info(f"📊 Validating promotion:")
        logger.info(f"   Current metrics: {current_metrics}")
        logger.info(f"   New metrics: {new_metrics}")

        # 1. Проверяем наличие метрик
        if not current_metrics:
            raise ValueError(
                f"Current model {current_model.id} has no metrics, cannot compare"
            )

        if not new_metrics:
            raise ValueError(
                f"New model {new_model.id} has no metrics, promotion rejected"
            )

        # 2. Определяем метрику (приоритет: rmse -> mae -> r2 -> accuracy)
        possible_metrics = ["rmse", "mae", "mape", "r2", "accuracy"]

        metric_name = None
        for m in possible_metrics:
            if m in current_metrics and m in new_metrics:
                metric_name = m
                break

        if not metric_name:
            raise ValueError(
                f"No common metrics found. "
                f"Current metrics: {list(current_metrics.keys())}, "
                f"New metrics: {list(new_metrics.keys())}"
            )

        # 3. Для метрик ошибки (RMSE, MAE, MAPE) — чем меньше, тем лучше
        lower_is_better_metrics = {"rmse", "mae", "mape"}

        current_value = current_metrics[metric_name]
        new_value = new_metrics[metric_name]

        logger.info(f"   Comparing {metric_name}: current={current_value:.6f}, new={new_value:.6f}")

        # 4. Сравниваем в зависимости от типа метрики
        if metric_name in lower_is_better_metrics:
            # Чем меньше — тем лучше
            if new_value > current_value:
                error_msg = (
                    f"Promotion rejected: new model has worse {metric_name} "
                    f"({new_value:.6f} > {current_value:.6f})"
                )
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
            elif new_value == current_value:
                error_msg = (
                    f"Promotion rejected: new model has equal {metric_name} "
                    f"({new_value:.6f} == {current_value:.6f}) - no improvement"
                )
                logger.warning(f"⚠️ {error_msg}")
                raise ValueError(error_msg)
            else:
                improvement = (current_value - new_value) / current_value * 100
                logger.info(f"   ✅ {metric_name} improved by {improvement:.4f}%")
        else:
            # Чем больше — тем лучше (accuracy, r2, auc)
            if new_value < current_value:
                error_msg = (
                    f"Promotion rejected: new model has worse {metric_name} "
                    f"({new_value:.6f} < {current_value:.6f})"
                )
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
            elif new_value == current_value:
                error_msg = (
                    f"Promotion rejected: new model has equal {metric_name} "
                    f"({new_value:.6f} == {current_value:.6f}) - no improvement"
                )
                logger.warning(f"⚠️ {error_msg}")
            elif new_value == current_value:
                logger.info(f"   ⚠️ {metric_name} is equal ({new_value:.6f} == {current_value:.6f})")
                logger.info(f"   ✅ Promotion allowed (equal metrics, but may have other benefits)")
            else:
                improvement = (new_value - current_value) / current_value * 100
                logger.info(f"   ✅ {metric_name} improved by {improvement:.4f}%")