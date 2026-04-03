# app/ml/self_healing/retrain_detector.py

"""
Detects when retrain is needed and creates recommendations.
Pure detection — no automatic training.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from models.ml_model import MLModel
from models.industrial_dataset import IndustrialDatasetRaw

logger = logging.getLogger("promo_ml")


class RetrainDetector:
    """
    Detects conditions that warrant model retraining.
    Returns recommendations without executing training.
    """

    # Конфигурация порогов
    NEW_DATA_THRESHOLD = 50  # новых записей
    DAYS_SINCE_TRAIN_WARNING = 1  # дней для рекомендации
    DAYS_SINCE_TRAIN_CRITICAL = 14  # дней для срочной рекомендации

    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()
        self._own_session = db is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._own_session:
            self.db.close()

    def check_and_recommend(self) -> Dict[str, Any]:
        """
        Проверяет все условия и возвращает рекомендацию.

        Returns:
            dict: {
                "needed": bool,
                "reason": str | None,
                "priority": "high" | "medium" | "low" | None,
                "candidate_metrics": dict | None,
                "new_data_count": int,
                "days_since_train": int | None
            }
        """
        try:
            # Получаем активную модель
            active_model = self.db.query(MLModel).filter(
                MLModel.is_active == True,
                MLModel.is_deleted == False
            ).first()

            # Считаем новые данные
            new_data_count = self._count_new_data(active_model)

            # Считаем дни с последнего обучения
            days_since_train = self._days_since_last_train(active_model)

            # Проверяем условия
            priority = None
            reason = None
            needed = False

            # 1. Новые данные (высокий приоритет)
            if new_data_count >= self.NEW_DATA_THRESHOLD:
                needed = True
                priority = "high"
                reason = f"📊 New data available: {new_data_count} new rows since last training"

            # 2. Давно не обучали (средний приоритет)
            elif days_since_train and days_since_train >= self.DAYS_SINCE_TRAIN_WARNING:
                needed = True
                priority = "medium" if days_since_train < self.DAYS_SINCE_TRAIN_CRITICAL else "high"
                reason = f"⏰ No training for {days_since_train} days"

            # 3. Нет активной модели (первое обучение)
            elif not active_model:
                needed = True
                priority = "high"
                reason = "🎯 No active model found — initial training required"

            return {
                "needed": needed,
                "reason": reason,
                "priority": priority,
                "candidate_metrics": None,  # будет заполнено после предобучения
                "new_data_count": new_data_count,
                "days_since_train": days_since_train,
                "active_model_id": active_model.id if active_model else None,
                "active_model_version": active_model.version if active_model else None,
            }

        except Exception as e:
            logger.error(f"Failed to check retrain need: {e}")
            return {
                "needed": False,
                "reason": None,
                "priority": None,
                "candidate_metrics": None,
                "new_data_count": 0,
                "days_since_train": None,
                "error": str(e),
            }

    def _count_new_data(self, active_model: Optional[MLModel]) -> int:
        """Считает количество новых записей после последнего обучения"""
        if not active_model:
            # Нет активной модели — считаем все данные как "новые"
            return self.db.query(IndustrialDatasetRaw).count()

        return self.db.query(IndustrialDatasetRaw).filter(
            IndustrialDatasetRaw.created_at > active_model.created_at
        ).count()

    def _days_since_last_train(self, active_model: Optional[MLModel]) -> Optional[int]:
        """Возвращает количество дней с последнего обучения"""
        if not active_model:
            return None

        delta = datetime.now(timezone.utc) - active_model.created_at
        return delta.days