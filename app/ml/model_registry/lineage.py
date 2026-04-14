# app/ml/model_registry/lineage.py
# — MODEL LINEAGE UTILITIES  (Родословная моделей + события)

# app/ml/model_registry/lineage.py

import logging
from pathlib import Path
import json
import os
from typing import Optional, Dict, Any, Union
from datetime import datetime, timezone
from app.core.settings import settings

logger = logging.getLogger("promo_ml")

# ==========================================================
# Static lineage (meta-level)
# ==========================================================

def get_current_model_id() -> Optional[str]:
    """
    Возвращает model_id текущей активной модели.
    Читает из файла models/current/*.meta.json
    """
    # Используем settings.ML_MODEL_DIR
    models_dir = Path(settings.ML_MODEL_DIR).parent
    current_dir = models_dir / "current"

    if not current_dir.exists():
        return None

    # Ищем любой .meta.json файл в current
    meta_files = list(current_dir.glob("*.meta.json"))
    if not meta_files:
        return None

    # Берём первый попавшийся
    with open(meta_files[0], "r") as f:
        meta = json.load(f)

    return str(meta.get("model_id"))


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
# Runtime lineage (event-level)
# ==========================================================

def get_lineage_events_file() -> Path:
    """
    Возвращает путь к lineage events файлу.
    """
    history_dir = Path(settings.ML_LINEAGE_DIR)
    print(f"🔴 Base dir: {history_dir}")

    history_dir.mkdir(parents=True, exist_ok=True)

    return history_dir / "lineage_events.json"



def get_current_metrics() -> dict:
    """Возвращает текущие метрики активной модели"""
    current_metrics_file = Path(settings.ML_MODEL_DIR).parent / "current.metrics.json"
    if current_metrics_file.exists():
        with open(current_metrics_file) as f:
            return json.load(f)
    return {}



def record_lineage_event(
        event_type: str,
        model_id: str,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Записывает runtime lineage событие (rollback, promotion, trained, etc.)
    """
    logger.info(f"🔴 RECORD_LINEAGE_EVENT CALLED: {event_type}, model_id={model_id}")

    lineage_file = get_lineage_events_file()

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

    # Оставляем только последние 1000 событий
    if len(events) > 1000:
        events = events[-1000:]

    with open(lineage_file, "w") as f:
        json.dump(events, f, indent=2)