# app/ml/model_registry/rollback.py
# — MODEL ROLLBACK (current → archive) + lineage event

from pathlib import Path
from datetime import datetime, timezone
import shutil
import json
import os

from app.ml.model_registry.lineage import record_lineage_event


def _safe_timestamp() -> str:
    """
    Filesystem-safe UTC timestamp.
    Windows-compatible.
    """
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def rollback_current_to_archive(
    model_id: str | None = None,
) -> dict:
    """
    Откатывает current-модель к версии из archive.

    Если model_id не задан:
    - берётся последняя версия из archive (по времени модификации)

    Возвращает информацию о выполненном rollback.
    """

    models_dir = Path(os.getenv("MODELS_DIR", "models"))

    current_dir = models_dir / "current"
    archive_dir = models_dir / "archive"

    if not archive_dir.exists():
        raise RuntimeError("Archive directory does not exist")

    archived_dirs = sorted(
        [p for p in archive_dir.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not archived_dirs:
        raise RuntimeError("No archived models available for rollback")

    # ==========================================================
    # Выбор целевой версии
    # ==========================================================

    if model_id:
        target_dir = archive_dir / model_id
        if not target_dir.exists():
            raise RuntimeError(f"Archived model '{model_id}' not found")
    else:
        target_dir = archived_dirs[0]

    target_dir_name = target_dir.name

    # ==========================================================
    # Backup current → archive/rollback_<timestamp>
    # ==========================================================

    if current_dir.exists() and current_dir.is_dir():
        rollback_id = _safe_timestamp()
        rollback_dir = archive_dir / f"rollback_{rollback_id}"

        if rollback_dir.exists():
            raise RuntimeError("Rollback backup directory already exists")

        shutil.move(str(current_dir), str(rollback_dir))

    # ==========================================================
    # Restore target → current
    # ==========================================================

    shutil.copytree(target_dir, current_dir)

    # ==========================================================
    # Update meta with rollback info
    # ==========================================================

    meta_path = current_dir / "model.meta.json"
    restored_model_id = None

    if meta_path.exists():
        with open(meta_path, "r") as f:
            meta = json.load(f)

        restored_model_id = meta.get("model_id")

        meta["rollback_at"] = datetime.now(timezone.utc).isoformat()
        meta["rolled_back_from"] = target_dir_name

        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

    # ==========================================================
    # 🔥 Stage 4: record lineage event
    # ==========================================================

    record_lineage_event(
        event_type="rollback",
        model_id=restored_model_id or target_dir_name,
        reason="manual_or_auto",
        metadata={
            "restored_from_archive_dir": target_dir_name,
        },
    )

    return {
        "rollback_performed": True,
        "restored_model_id": restored_model_id or target_dir_name,
        "source_archive_dir": target_dir_name,
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