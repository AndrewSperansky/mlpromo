# app/api/v1/ml/router.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil
import tempfile
import zipfile
import json
from datetime import datetime, timezone

from app.ml.model_registry.promotion_policy import decide_promotion
from app.ml.train.train_pipeline import train_pipeline

router = APIRouter()

BASE_DIR = Path("app/models")
ARCHIVE_DIR = BASE_DIR / "archive"
LINEAGE_FILE = BASE_DIR / "lineage_events.json"

ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


# =========================================
# Utils
# =========================================

def record_lineage_event(event_type: str, model_id: str, metadata: dict):
    LINEAGE_FILE.parent.mkdir(parents=True, exist_ok=True)

    if LINEAGE_FILE.exists():
        with open(LINEAGE_FILE) as f:
            events = json.load(f)
    else:
        events = []

    events.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "model_id": model_id,
        "metadata": metadata
    })

    with open(LINEAGE_FILE, "w") as f:
        json.dump(events, f, indent=2)


def get_current_metrics():
    current_metrics_file = BASE_DIR / "current.metrics.json"
    if current_metrics_file.exists():
        with open(current_metrics_file) as f:
            return json.load(f)
    return {}


# =========================================
# Upload + Decision
# =========================================

@router.post("/models/upload")
def upload_model_bundle(file: UploadFile = File(...)):

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files allowed")

    with tempfile.TemporaryDirectory() as tmp_dir:

        tmp_zip_path = Path(tmp_dir) / file.filename

        with open(tmp_zip_path, "wb") as f:
            f.write(file.file.read())

        with zipfile.ZipFile(tmp_zip_path, "r") as zip_ref:
            zip_ref.extractall(tmp_dir)

        model_file = Path(tmp_dir) / "cb_promo_v1.cbm"
        meta_file = Path(tmp_dir) / "cb_promo_v1.meta.json"
        metrics_file = Path(tmp_dir) / "metrics.json"

        if not model_file.exists():
            raise HTTPException(status_code=400, detail="cb_promo_v1.cbm missing")

        if not meta_file.exists():
            raise HTTPException(status_code=400, detail="cb_promo_v1.meta.json missing")

        if not metrics_file.exists():
            raise HTTPException(status_code=400, detail="metrics.json missing")

        with open(meta_file) as f:
            meta = json.load(f)

        with open(metrics_file) as f:
            metrics = json.load(f)

        model_id = meta.get("model_id")
        if not model_id:
            raise HTTPException(status_code=400, detail="model_id missing")

        target_model = ARCHIVE_DIR / f"{model_id}.cbm"
        target_meta = ARCHIVE_DIR / f"{model_id}.meta.json"
        target_metrics = ARCHIVE_DIR / f"{model_id}.metrics.json"

        if target_model.exists():
            raise HTTPException(status_code=400, detail="Model already exists")

        shutil.move(str(model_file), target_model)
        shutil.move(str(meta_file), target_meta)
        shutil.move(str(metrics_file), target_metrics)

        decision = decide_promotion(
            candidate_metrics=metrics,
            current_metrics=get_current_metrics(),
        )

        record_lineage_event(
            "upload",
            model_id,
            {"decision": decision}
        )

        return {
            "status": "uploaded",
            "model_id": model_id,
            "promotion_decision": decision
        }



# ========================================
# TRAIN TRIGGER
# ========================================

@router.post("/train")
def trigger_training(promote: bool = True):
    return train_pipeline(
        promote=promote,
        trigger="admin_ui",
    )


# =========================================
# Evaluate отдельно
# =========================================

@router.post("/models/evaluate/{model_id}")
def evaluate_model(model_id: str):

    metrics_file = ARCHIVE_DIR / f"{model_id}.metrics.json"

    if not metrics_file.exists():
        raise HTTPException(status_code=404, detail="Model not found")

    with open(metrics_file) as f:
        metrics = json.load(f)

    decision = decide_promotion(
        candidate_metrics=metrics,
        current_metrics=get_current_metrics(),
    )

    record_lineage_event(
        "evaluate",
        model_id,
        {"decision": decision}
    )

    return {
        "model_id": model_id,
        "promotion_decision": decision
    }


# =========================================
# Rollback
# =========================================

@router.post("/models/rollback/{model_id}")
def rollback_model(model_id: str):

    source_model = ARCHIVE_DIR / f"{model_id}.cbm"
    source_meta = ARCHIVE_DIR / f"{model_id}.meta.json"
    source_metrics = ARCHIVE_DIR / f"{model_id}.metrics.json"

    if not source_model.exists():
        raise HTTPException(status_code=404, detail="Model not found")

    shutil.copy(source_model, BASE_DIR / "current.cbm")
    shutil.copy(source_meta, BASE_DIR / "current.meta.json")
    shutil.copy(source_metrics, BASE_DIR / "current.metrics.json")

    record_lineage_event(
        "rollback",
        model_id,
        {}
    )

    return {
        "status": "rolled_back",
        "model_id": model_id
    }


# =========================================
# Lineage
# =========================================

@router.get("/models/lineage")
def get_lineage():

    if not LINEAGE_FILE.exists():
        return []

    with open(LINEAGE_FILE) as f:
        return json.load(f)