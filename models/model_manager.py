# models/model_manager.py

from pathlib import Path
from datetime import datetime, timezone
import shutil
import os


ARTIFACT_FILES = [
    "model.cbm",
    "model.meta.json",
    "shap_summary.json",
]


def _base_models_dir() -> Path:
    """
    Возвращает актуальный MODELS_DIR из окружения
    """
    return Path(os.getenv("MODELS_DIR", "models"))  # ← NEW


def ensure_dirs():
    base = _base_models_dir()                        # ← NEW
    (base / "current").mkdir(parents=True, exist_ok=True)
    (base / "archive").mkdir(parents=True, exist_ok=True)
    (base / "baseline").mkdir(parents=True, exist_ok=True)


def archive_current_model():
    """
    Архивирует текущую модель (если она есть)
    """
    base = _base_models_dir()                        # ← NEW
    current = base / "current"
    archive = base / "archive"

    if not (current / "model.cbm").exists():
        return None

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    target_dir = archive / ts
    target_dir.mkdir(parents=True, exist_ok=True)

    for fname in ARTIFACT_FILES:
        src = current / fname
        if src.exists():
            shutil.copy2(src, target_dir / fname)

    return target_dir


def promote_candidate(candidate_dir: Path):
    """
    Делает candidate → current
    """
    ensure_dirs()

    base = _base_models_dir()                        # ← NEW
    current = base / "current"

    archive_current_model()

    for fname in ARTIFACT_FILES:
        src = candidate_dir / fname
        if src.exists():
            shutil.copy2(src, current / fname)
