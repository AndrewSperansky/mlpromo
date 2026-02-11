# app/ml/model_registry/lineage.py
# — MODEL LINEAGE UTILITIES  (Родословная моделей + события)

from pathlib import Path
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime, timezone


# ==========================================================
# Static lineage (meta-level)
# ==========================================================

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

    meta["parent_model_id"] = parent_model_id
    meta["trigger"] = trigger

    return meta


# ==========================================================
# Runtime lineage (event-level, Stage 4)
# ==========================================================

def _get_lineage_events_file() -> Path:
    """
    Возвращает путь к lineage events файлу.
    """
    base_dir = Path(os.getenv("MODELS_DIR", "models"))
    history_dir = base_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    return history_dir / "lineage_events.json"


def record_lineage_event(
    event_type: str,
    model_id: str,
    reason: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Записывает runtime lineage событие (rollback, promotion и т.д.)
    """

    lineage_file = _get_lineage_events_file()

    if lineage_file.exists():
        with open(lineage_file, "r") as f:
            events = json.load(f)
    else:
        events = []

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "model_id": model_id,
        "reason": reason,
        "metadata": metadata or {},
    }

    events.append(event)

    with open(lineage_file, "w") as f:
        json.dump(events, f, indent=2)
