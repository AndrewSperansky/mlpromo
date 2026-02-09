# app/ml/model_registry/lineage.py
# — MODEL LINEAGE UTILITIES  (Родословная моделей)

from pathlib import Path
import json
import os
from typing import Optional


def get_current_model_id() -> Optional[str]:
    """
    Возвращает model_id текущей active модели (current).
    """
    models_dir = Path(os.getenv("MODELS_DIR", "models"))
    meta_path = models_dir / "current" / "model.meta.json"

    if not meta_path.exists():
        return None

    with open(meta_path, "r") as f:
        meta = json.load(f)

    return meta.get("model_id")


def enrich_meta_with_lineage(
    meta: dict,
    trigger: str,
) -> dict:
    """
    Добавляет lineage-информацию в meta.
    """

    parent_model_id = get_current_model_id()

    meta["parent_model_id"] = parent_model_id  # ✨ NEW
    meta["trigger"] = trigger                  # ✨ NEW

    return meta
