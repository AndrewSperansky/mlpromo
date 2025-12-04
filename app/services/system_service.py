"""
System Service: технические методы системы.
"""

from datetime import datetime


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
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
        }
