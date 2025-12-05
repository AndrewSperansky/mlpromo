# app/core/logger.py
import logging


class CorrelationIdFilter(logging.Filter):
    """Добавляет correlation_id во все записи логов."""

    def filter(self, record):
        if not hasattr(record, "correlation_id"):
            record.correlation_id = None
        return True


def attach_correlation_filter(logger: logging.Logger):
    """Добавляет фильтр корреляции на логгер и все его хэндлеры."""
    filt = CorrelationIdFilter()
    logger.addFilter(filt)
    for handler in logger.handlers:
        handler.addFilter(filt)
