import logging
import logging.config
from pathlib import Path

# Создаём директорию logs, если её нет
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"},
        "uvicorn": {"format": "%(levelprefix)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": str(LOG_FILE),
            "maxBytes": 5_000_000,  # 5 MB
            "backupCount": 5,
            "encoding": "utf-8",
            "level": "INFO",
        },
    },
    "loggers": {
        "promo_ml": {  # наш основной логгер
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "INFO",
        },
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


def setup_logging():
    """Инициализация логирования."""
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger("promo_ml")
    logger.info("Logging successfully configured.")
    return logger
