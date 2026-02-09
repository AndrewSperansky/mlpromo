# app/ml/model_registry/rollback.py
# — MODEL ROLLBACK (current → archive)

from pathlib import Path
from datetime import datetime, timezone
import shutil
import json
import os


def _safe_timestamp() -> str:
    """
    Filesystem-safe UTC timestamp.
    Windows-compatible.
    """
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")  # ✨ NEW


def rollback_current_to_archive(
    model_id: str | None = None,
) -> dict:
    """
    Откатывает current-модель к предыдущей версии из archive.

    Если model_id не задан:
    - берётся последняя версия из archive (по времени)
    """

    models_dir = Path(os.getenv("MODELS_DIR", "models"))

    current_dir = models_dir / "current"
    archive_dir = models_dir / "archive"

    if not archive_dir.exists():
        raise RuntimeError("Archive directory does not exist")

    archived_models = sorted(
        [p for p in archive_dir.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not archived_models:
        raise RuntimeError("No archived models available for rollback")

    # ✨ NEW: выбор версии
    if model_id:
        target_dir = archive_dir / model_id
        if not target_dir.exists():
            raise RuntimeError(f"Archived model {model_id} not found")
    else:
        target_dir = archived_models[0]

    # ✨ NEW: бэкап текущей модели перед rollback
    if current_dir.exists():
        rollback_id = _safe_timestamp()  # ✨ NEW
        rollback_dir = archive_dir / f"rollback_{rollback_id}"

        rollback_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(current_dir), rollback_dir)

    # ✨ NEW: восстановление выбранной версии
    shutil.copytree(target_dir, current_dir)

    # ✨ NEW: фиксация rollback в meta
    meta_path = current_dir / "model.meta.json"
    if meta_path.exists():
        with open(meta_path, "r") as f:
            meta = json.load(f)

        meta["rollback_at"] = datetime.now(timezone.utc).isoformat()
        meta["rolled_back_from"] = target_dir.name

        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

    return {
        "rollback_performed": True,
        "restored_model_id": target_dir.name,
    }


"""
Что делает файл:

Берёт MODELS_DIR
Ищет:
models/current
models/archive/*

Выбирает:
либо конкретный model_id
либо последнюю archived-модель

Безопасно:
текущую модель сохраняет в archive/rollback_*
Восстанавливает выбранную версию в current
Обновляет model.meta.json
"""