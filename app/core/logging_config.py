import logging
import logging.config
from pathlib import Path
from pythonjsonlogger import jsonlogger

# ---------------------------------------------------------
# Создание директории logs/
# ---------------------------------------------------------
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"

# ---------------------------------------------------------
# Конфигурация логирования
# ---------------------------------------------------------
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        # JSON-формат для продакшена и docker
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s "
                   "%(module)s %(funcName)s %(lineno)d "
                   "%(request_id)s %(model_version)s"
        },

        # Стандартный формат (для fallback, если JSON отключат)
        "default": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        },
    },

    "handlers": {
        # Консоль (docker / dev)
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": "INFO",
        },

        # Файл с ротацией
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": str(LOG_FILE),
            "maxBytes": 10_000_000,  # 10 MB
            "backupCount": 5,
            "encoding": "utf-8",
            "level": "INFO",
        },
    },

    "loggers": {
        # Главный логгер проекта
        "promo_ml": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },

        # Логи uvicorn (попадают в консоль)
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console"]
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        },
    },
}

# ---------------------------------------------------------
# Функция инициализации
# ---------------------------------------------------------
def setup_logging() -> logging.Logger:
    """Настройка системы логирования приложения."""
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger("promo_ml")
    logger.info("Logging configured and active.")
    return logger
