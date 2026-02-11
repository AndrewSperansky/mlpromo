# app/ml/monitoring/latency_actions.py
# — AUTOMATIC ROLLBACK ON LATENCY BREACH
# делает одно: 👉 восстановить current из последнего archive


from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
import os
import shutil


def _get_models_dir() -> Path:
    return Path(os.getenv("MODELS_DIR", "models"))


def rollback_current_to_previous() -> Dict[str, Any]:
    """
    Rollback current → latest archive version
    """

    models_dir = _get_models_dir()
    current_dir = models_dir / "current"
    archive_dir = models_dir / "archive"

    if not archive_dir.exists():
        return {"status": "no_archive"}

    archived_versions = sorted(
        [p for p in archive_dir.iterdir() if p.is_dir()],
        reverse=True,
    )

    if not archived_versions:
        return {"status": "no_versions"}

    latest_archive = archived_versions[0]

    # очищаем current
    for file in current_dir.iterdir():
        if file.is_file():
            file.unlink()

    # восстанавливаем из архива
    for file in latest_archive.iterdir():
        shutil.copy(file, current_dir / file.name)

    return {
        "status": "rolled_back",
        "rollback_to": latest_archive.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
