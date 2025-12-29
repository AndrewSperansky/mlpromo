"""
System Service: технические методы системы.
"""

from datetime import datetime, timezone
import logging
from app.core.config import settings
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("promo_ml")


class SystemService:
    """
    Сервис системных операций: health-check, метаинформация и пр.
    """

    @staticmethod
    def health_check() -> dict:
        """
        Возвращает состояние системы.

        Returns:
            dict: Статус сервиса и текущее время.
        """
        logger.info("Healthcheck executed")

        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "promo-ml",
        }

    @staticmethod
    def health_db(self, db: Session) -> dict:

        db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "checks": {
                "database": "ok",
                "config": "ok",
            },
            "environment": settings.ENV,
            "version": settings.VERSION,
        }
