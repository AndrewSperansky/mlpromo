# app/api/v1/ml/router.py


import shutil
import json
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from pathlib import Path
from datetime import datetime


from app.db.session import get_db
from app.ml.runtime_state import ML_RUNTIME_STATE
from app.services.ml_training_service import MLTrainingService
from app.services.ml_prediction_service import MLPredictionService
from app.ml.model_registry.lineage import record_lineage_event

from app.api.v1.ml.schemas import (
    PredictionRequest,
    PredictionResponse,
    OneCPredictRequest,
    OneCPredictResponse,
)




router = APIRouter(tags=["ml"])

MODELS_DIR = Path("models/current")
ARCHIVE_DIR = Path("models/archive")


# ========== DEPENDENCIES ==========


def get_prediction_service() -> MLPredictionService:
    """
    Возвращает сервис предсказаний.
    Модель загружается ВНУТРИ сервиса.
    """
    return MLPredictionService()


def get_training_service() -> MLTrainingService:
    return MLTrainingService()


# ========== ENDPOINTS ==========


@router.post(
    "/predict",
    summary="ML предсказание + SHAP",
    response_model=PredictionResponse,
)

def predict(
    payload: PredictionRequest,
    svc: MLPredictionService = Depends(get_prediction_service),
):
    """
    Выполняет ML-предсказание.

    PredictionRequest (вход):
    - prediction_date
    - price
    - discount
    - avg_sales_7d
    - promo_days_left
    - promo_code
    - sku
    """



    result = svc.predict(payload)


    return result


# @router.post("/train", summary="Обучение ML модели")
# def train_model(
#     dataset_path: str,
#     svc: MLTrainingService = Depends(get_training_service),
# ):
#     """
#     Запускает обучение ML модели.
#     """
    # return svc.train(dataset_path=dataset_path)
    # pass


@router.get("/dataset", summary="ML dataset (read-only)")
def get_ml_dataset(
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Читает витрину promo_ml_dataset_v1
    """
    query = text("""
        SELECT
            date,
            promo_code,
            sku,
            price,
            discount,
            target_sales_qty,
            avg_sales_7d,
            avg_discount_7d,
            promo_days_left
        FROM promo_ml_dataset_v1
        ORDER BY date, promo_code, sku
        LIMIT :limit
        OFFSET :offset
    """)

    rows = db.execute(
        query,
        {"limit": limit, "offset": offset},
    ).mappings().all()

    return {
        "count": len(rows),
        "items": rows,
    }


@router.get("/model-status")
def model_status():
    return {
        "checked": ML_RUNTIME_STATE["checked"],
        "status": ML_RUNTIME_STATE["status"],
        "model_loaded": ML_RUNTIME_STATE["model_loaded"],
        "ml_model_id": ML_RUNTIME_STATE["ml_model_id"],
        "version": ML_RUNTIME_STATE["version"],
        "checksum_verified": ML_RUNTIME_STATE["checksum_verified"],
        "errors": ML_RUNTIME_STATE.get("errors", []),
        "warnings": ML_RUNTIME_STATE.get("warnings", []),
    }


@router.post("/1c/predict", response_model=OneCPredictResponse)
def predict_from_1c(
    payload: OneCPredictRequest,
    db: Session = Depends(get_db),
    svc: MLPredictionService = Depends(),
):
    if not ML_RUNTIME_STATE.get("model_loaded"):
        raise HTTPException(status_code=503, detail="ML model not ready")

    # idempotency
    exists = db.execute(
        text("SELECT 1 FROM ml_prediction_request WHERE id = :id"),
        {"id": payload.request_id},
    ).first()

    if exists:
        raise HTTPException(status_code=409, detail="Request already processed")

    # store request
    db.execute(
        text("""
        INSERT INTO ml_prediction_request (id, source, payload)
        VALUES (:id, '1C', CAST(:payload AS JSONB))
        """),
        {
            "id": str(payload.request_id),    # ← убедитесь, что UUID → str
            "payload": json.dumps(payload.data)  # ← dict → JSON-строка
        },
    )

    # predict
    prediction, shap = svc.predict_raw(payload.data)

    # store result
    db.execute(
        text("""
        INSERT INTO ml_prediction_result
        (request_id, model_id, model_version, prediction_value, shap_values)
        VALUES (:rid, :mid, :ver, :pred, CAST(:shap AS JSONB))
        """),
        {
            "rid": str(payload.request_id),
            "mid": ML_RUNTIME_STATE["ml_model_id"],
            "ver": ML_RUNTIME_STATE["version"],
            "pred": prediction,
            "shap": json.dumps(shap),
        },

    )

    db.commit()

    return OneCPredictResponse(
        request_id=payload.request_id,
        prediction=prediction,
        ml_model_id=ML_RUNTIME_STATE["ml_model_id"],
        version=ML_RUNTIME_STATE["version"],
    )


# =========================
# MODEL REGISTRY
# =========================


@router.get("/models")
def list_models():
    models = []

    active_ml_model_id = ML_RUNTIME_STATE.get("ml_model_id")

    # Active model(s)
    if MODELS_DIR.exists():
        for file in MODELS_DIR.glob("*.cbm"):
            models.append({
                "ml_model_id": file.stem,
                "version": ML_RUNTIME_STATE.get("version"),
                "active": file.stem == active_ml_model_id,
                "created_at": datetime.fromtimestamp(
                    file.stat().st_mtime
                ).isoformat()
            })

    # Archived models
    if ARCHIVE_DIR.exists():
        for file in ARCHIVE_DIR.glob("*.cbm"):
            models.append({
                "ml_model_id": file.stem,
                "version": "archived",
                "active": file.stem == active_ml_model_id,
                "created_at": datetime.fromtimestamp(
                    file.stat().st_mtime
                ).isoformat()
            })

    return models


@router.post("/models/{ml_model_id}/activate")
def activate_model(ml_model_id: str):
    archive_model = ARCHIVE_DIR / f"{ml_model_id}.cbm"

    if not archive_model.exists():
        raise HTTPException(status_code=404, detail="Model not found")

    # Ensure current dir exists
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Remove current model(s)
    for file in MODELS_DIR.glob("*.cbm"):
        file.unlink()

    # Copy archive model to current
    shutil.copy(
        archive_model,
        MODELS_DIR / archive_model.name
    )

    # 🔥 Обновляем runtime state
    ML_RUNTIME_STATE["ml_model_id"] = ml_model_id
    ML_RUNTIME_STATE["version"] = "manual-activation"
    ML_RUNTIME_STATE["model_loaded"] = False  # форс reload при следующем predict

    return {
        "status": "activated",
        "ml_model_id": ml_model_id
    }


# =========================
# MODEL UPLOAD (LITE VERSION)
# =========================

from fastapi import UploadFile, File
import zipfile
import tempfile

@router.post("/models/upload")
def upload_model_bundle(file: UploadFile = File(...)):
    """
    Upload model bundle (zip).
    Required inside zip:
        - model.cbm
        - model.meta.json
        - metrics.json

    Lite version:
        сохраняем файлы в archive без изменения структуры.
    """

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files allowed")

    with tempfile.TemporaryDirectory() as tmp_dir:

        tmp_zip_path = Path(tmp_dir) / file.filename

        # Save uploaded file
        with open(tmp_zip_path, "wb") as f:
            f.write(file.file.read())

        # Extract
        with zipfile.ZipFile(tmp_zip_path, "r") as zip_ref:
            zip_ref.extractall(tmp_dir)

        model_file = Path(tmp_dir) / "model.cbm"
        meta_file = Path(tmp_dir) / "model.meta.json"
        metrics_file = Path(tmp_dir) / "metrics.json"

        if not model_file.exists():
            raise HTTPException(status_code=400, detail="model.cbm missing")

        if not meta_file.exists():
            raise HTTPException(status_code=400, detail="model.meta.json missing")

        if not metrics_file.exists():
            raise HTTPException(status_code=400, detail="metrics.json missing")

        # Load meta
        with open(meta_file) as f:
            meta = json.load(f)

        model_id = meta.get("model_id")

        if not model_id:
            raise HTTPException(status_code=400, detail="model_id missing in meta")

        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

        # Target paths (Lite format)
        target_model = ARCHIVE_DIR / f"{model_id}.cbm"
        target_meta = ARCHIVE_DIR / f"{model_id}.meta.json"
        target_metrics = ARCHIVE_DIR / f"{model_id}.metrics.json"

        if target_model.exists():
            raise HTTPException(status_code=400, detail="Model already exists in archive")

        # Move files
        shutil.move(str(model_file), target_model)
        shutil.move(str(meta_file), target_meta)
        shutil.move(str(metrics_file), target_metrics)

        # Record lineage event
        record_lineage_event(
            event_type="upload",
            model_id=model_id,
            metadata={"storage": "archive_flat"},
        )

        return {
            "status": "uploaded",
            "model_id": model_id,
        }