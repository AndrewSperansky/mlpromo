import logging
import logging.config
import json
from pythonjsonlogger import jsonlogger

def setup_logging():
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter()

    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
