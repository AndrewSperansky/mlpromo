# app/api/ml/model_loader.py
import os
import logging
from pathlib import Path
import joblib

logger = logging.getLogger("promo_ml")
MODEL_PATH = Path("data/models_history/latest_model.pkl")

def load_model():
    if MODEL_PATH.exists():
        logger.info(f"Loading model from {MODEL_PATH}")
        return joblib.load(MODEL_PATH)
    logger.warning("Model not found, returning None placeholder")
    return None
