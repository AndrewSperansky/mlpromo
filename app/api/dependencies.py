# app/api/dependencies.py
from functools import lru_cache
from typing import Any
from app.api.ml.model_loader import load_model  # путь подкорректируй если нужно

@lru_cache()
def get_model() -> Any:
    # load_model должен возвращать объект модели/обёртку
    return load_model()
