# models/model_manager.py

import shutil
import os
from pathlib import Path
from datetime import datetime, timezone
from app.core.settings import settings



ARTIFACT_FILES = [
    "cb_promo_v1.cbm",
    "cb_promo_v1.meta.json",
    "shap_summary.json",
]



def ensure_dirs():

    current_dir = Path(settings.ML_CURRENT_DIR)  # /app/models/current
    candidate_dir = Path(settings.ML_CANDIDATE_DIR)  # /app/models/candidate
    metrics_dir = Path(settings.ML_METRICS_DIR)  # /app/models/metrics
    archive_dir = Path(settings.ML_ARCHIVE_DIR)

    current_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)


def archive_current_model():
    """
    Архивирует текущую модель (если она есть)
    """

    ensure_dirs()

    current_dir = Path(settings.ML_CURRENT_DIR)
    archive_dir = Path(settings.ML_ARCHIVE_DIR)



    if not (current_dir / "cb_promo_v1.cbm").exists():
        return None

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    target_dir = archive_dir / ts
    target_dir.mkdir(parents=True, exist_ok=True)

    for fname in ARTIFACT_FILES:
        src = current_dir / fname
        if src.exists():
            shutil.copy2(src, target_dir / fname)

    return target_dir


def promote_candidate(candidate_dir: Path):
    """
    Делает candidate → current
    """
    ensure_dirs()


    current_dir = Path(settings.ML_CURRENT_DIR)



    archive_current_model()

    for fname in ARTIFACT_FILES:
        src = candidate_dir / fname
        if src.exists():
            shutil.copy2(src, current_dir / fname)
