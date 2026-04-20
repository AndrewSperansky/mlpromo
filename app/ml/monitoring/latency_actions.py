# app/ml/monitoring/latency_actions.py
# — AUTOMATIC ROLLBACK ON LATENCY BREACH
# делает одно: 👉 восстановить current из последнего archive

import os
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
from app.core.settings import settings


def ensure_dirs():

    current_dir = Path(settings.ML_CURRENT_DIR)  # /app/models/current
    candidate_dir = Path(settings.ML_CANDIDATE_DIR)  # /app/models/candidate
    metrics_dir = Path(settings.ML_METRICS_DIR)  # /app/models/metrics
    archive_dir = Path(settings.ML_ARCHIVE_DIR)

    current_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)


def rollback_current_to_previous() -> Dict[str, Any]:
    """
    Rollback current → latest archive version
    """
    current_dir = Path(settings.ML_CURRENT_DIR)
    archive_dir = Path(settings.ML_ARCHIVE_DIR)

    current_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

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
