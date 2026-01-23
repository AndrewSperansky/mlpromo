# app/api/dependencies.py
from functools import lru_cache
from typing import Any
from app.api.v1.ml.model_io import load_model

@lru_cache()
def get_model() -> Any:
    # load_model должен возвращать объект модели/обёртку
    return load_model()
