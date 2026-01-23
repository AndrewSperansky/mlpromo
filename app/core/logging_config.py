"""
Logging configuration for Promo ML Backend.
JSON logging + file + stdout.
"""

import logging
import logging.config
from pathlib import Path
from pythonjsonlogger import jsonlogger
from app.core.logger import attach_correlation_filter


# Создаем папку logs, если ее нет
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"


def get_logging_config() -> dict:
    """
    Конфигурация логирования в формате dictConfig.

    Returns:
        dict: Конфигурация для logging.config.dictConfig
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": (
                    "%(asctime)s %(levelname)s %(name)s %(message)s "
                    "%(filename)s %(funcName)s %(lineno)d %(correlation_id)s"
                ),
            },
            "simple": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "level": "INFO",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": str(LOG_FILE),
                "maxBytes": 10_000_000,
                "backupCount": 5,
                "encoding": "utf-8",
                "level": "INFO",
            },
        },
        "loggers": {
            "promo_ml": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }


def setup_logging() -> logging.Logger:
    """
    Инициализация системы логирования.

    Returns:
        logging.Logger: корневой логгер приложения
    """
    logging.config.dictConfig(get_logging_config())
    logger = logging.getLogger("promo_ml")

    attach_correlation_filter(logger)

    logger.info("Logging initialized")
    return logger
