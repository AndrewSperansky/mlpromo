"""
System Service: технические методы системы.
"""

from datetime import datetime
import logging

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
            "timestamp": datetime.now(datetime.timezon.utc).isoformat(),
            "service": "promo-ml",
        }
