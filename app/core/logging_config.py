# core/logging_config.py
import logging
from pythonjsonlogger import jsonlogger


def setup_logging():
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    # remove default handlers if any (avoid duplicate logs)
    if root.handlers:
        root.handlers = []
    root.addHandler(handler)
    root.setLevel(logging.INFO)
