# app/api/v1/ml/router.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from pathlib import Path
import shutil
import tempfile
import zipfile
import json
import uuid
from io import BytesIO
from uuid import UUID
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text, select, delete, and_

from app.db.session import get_db
from models.ml_model import MLModel

from app.core.settings import settings

from app.ml.model_registry.promotion_policy import decide_promotion

from app.services.ml_training_service import MLTrainingService
from app.services.ml_prediction_service import MLPredictionService
from app.ml.registry.service import ModelRegistryService


from models.dataset_version import DatasetVersion
from models.industrial_dataset import IndustrialDatasetRaw
from app.ml.contract_check import validate_industrial_contract

from app.ml.runtime_state import ML_RUNTIME_STATE
from app.schemas.dataset_schema import DatasetVersionResponse
from app.services.dataset_service import DatasetService


from app.api.v1.ml.schemas import (
    PredictionRequest,
    PredictionResponse,
    OneCPredictRequest,
    OneCPredictResponse,
    ShapValue,
)


router = APIRouter(tags=["ml"])


BASE_DIR = Path(settings.ML_MODEL_DIR)

MODELS_DIR = BASE_DIR / "current"
ARCHIVE_DIR = BASE_DIR / "archive"
LINEAGE_FILE = BASE_DIR / "lineage_events.json"

ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


# ========== DEPENDENCIES ==========


def get_prediction_service() -> MLPredictionService:
    """
    Возвращает сервис предсказаний.
    Модель загружается ВНУТРИ сервиса.
    """
    return MLPredictionService()


def get_training_service() -> MLTrainingService:
    return MLTrainingService()


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


# ============================ ENDPOINTS ===============================

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

training_service = MLTrainingService()


@router.post("/train")
def train_model(
    dataset_version_id: UUID,
    promote: bool = Query(False),
):

    result = training_service.train(
        dataset_version_id=dataset_version_id,
        promote=promote,
        trigger="api",
    )

    return result


# =========================================
# EVALUATE By Id
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

# =========================================
# Models
# =========================================

@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    """
    Возвращает список моделей из БД.
    """

    models = (
        db.query(MLModel)
        .filter(MLModel.is_deleted == False)
        .order_by(MLModel.created_at.desc())
        .all()
    )

    active_model_id = ML_RUNTIME_STATE.get("ml_model_id")

    return [
        {
            "ml_model_id": m.id,
            "name": m.name,
            "algorithm": m.algorithm,
            "version": m.version,
            "dataset_version_id": m.dataset_version_id,   # ← ДОБАВЛЕНО
            "is_active": m.is_active,
            "trained_at": m.trained_at,
            "trained_rows_count": m.trained_rows_count,   # ← ДОБАВЛЕНО
            "features": m.features,
            "metrics": m.metrics,
            "active_in_runtime": m.id == active_model_id
        }
        for m in models
    ]



# =========================================
# Promote via Registry (DB-driven)
# =========================================

@router.post("/models/{model_id}/promote")
def promote_model(
    model_id: int,
    db: Session = Depends(get_db),
    ):
    registry = ModelRegistryService(db)

    try:
        model = registry.promote_model(model_id)

        return {
            "status": "promoted",
            "model_id": model.id,
            "name": model.name,
            "version": model.version,
            "dataset_version_id": str(model.dataset_version_id),
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))




# ========================================
# PREDICT (FastAPI)
# =======================================

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
    """

    # Pydantic v2: преобразуем payload в dict
    input_data = payload.model_dump()

    # Получаем прогноз и shap от сервиса
    prediction_result, shap_list = svc.predict_raw(input_data)

    # Если ML сервис вернул float, оборачиваем в dict
    if isinstance(prediction_result, float):
        prediction_result = {
            "prediction": prediction_result,
            "baseline": None,
            "uplift": None,
            "fallback_used": False,
            "reason": None,
        }

    # Преобразуем shap в Pydantic объекты
    shap_objs = [ShapValue(feature=s["feature"], effect=s["effect"]) for s in shap_list]

    # Формируем response
    response = PredictionResponse(
        promo_code=payload.promo_code,
        sku=payload.sku,
        date=payload.prediction_date,
        prediction=prediction_result["prediction"],
        baseline=prediction_result["baseline"],
        uplift=prediction_result["uplift"],
        shap_values=shap_objs,  # список ShapValue
        ml_model_id=ML_RUNTIME_STATE["ml_model_id"],
        version=ML_RUNTIME_STATE["version"],
        trained_at=ML_RUNTIME_STATE.get("trained_at"),
        features=input_data,
        fallback_used=prediction_result["fallback_used"],
        reason=prediction_result["reason"],
    )

    return response

# =========================================
# 1C PREDICT
# =========================================


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

    # ✅ НОРМАЛИЗАЦИЯ ДО PREDICT
    normalized_features = svc.normalize_external_features(payload.data)

    # store request (сохраняем уже нормализованные данные!)
    db.execute(
        text("""
        INSERT INTO ml_prediction_request (id, source, payload)
        VALUES (:id, '1C', CAST(:payload AS JSONB))
        """),
        {
            "id": str(payload.request_id),
            "payload": json.dumps(normalized_features)
        },
    )

    # predict (strict validation теперь не упадёт)
    prediction, shap = svc.predict_raw(normalized_features)

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

# =========================================
# MODEL ACTIVATE
# =========================================

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


# =========================================
# Dataset
# =========================================

@router.get("/datasets", response_model=list[DatasetVersionResponse])
def list_datasets():

    service = DatasetService()
    return service.list_versions()


# =========================================
# DATASET UPLOAD
# =========================================


@router.post("/dataset/upload")
def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Читаем файл в байты
    content = file.file.read()

    df: pd.DataFrame | None = None
    detected_encoding: str | None = None

    # Пробуем сначала utf-8, потом cp1251
    for encoding in ("utf-8", "cp1251"):
        try:
            df = pd.read_csv(BytesIO(content), encoding=encoding)
            detected_encoding = encoding
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError("Не удалось прочитать CSV: поддерживаются только utf-8 или cp1251")

    # Преобразуем булевы поля
    BOOL_MAP = {"Да": True, "Нет": False, "да": True, "нет": False}
    for col in ["ManualCoefficientFlag", "IsNewSKU", "IsAnalogSKU"]:
        if col in df.columns:
            df[col] = df[col].map(BOOL_MAP).fillna(False)  # type: ignore

    # Валидация датасета
    validate_industrial_contract(df)

    # Создаём версию датасета
    dataset_version = DatasetVersion(
        id=uuid.uuid4(),
        row_count=len(df),
        status="READY"
    )
    db.add(dataset_version)
    db.flush()

    # Запись всех строк в raw таблицу
    records = df.to_dict(orient="records")
    for row in records:
        db_row = IndustrialDatasetRaw(
            dataset_version_id=dataset_version.id,
            **row
        )
        db.add(db_row)

    db.commit()

    return {
        "dataset_version": str(dataset_version.id),
        "rows_loaded": len(df),
        "detected_encoding": detected_encoding
    }

# =========================================
# DATASET DELETE
# =========================================


@router.delete("/datasets/{dataset_id}")
def delete_dataset(
        dataset_id: UUID,
        db: Session = Depends(get_db)
):
    # Находим версию датасета
    dataset = db.get(DatasetVersion, dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:

        # если нужно удалить только строки датасета
        # db.query(IndustrialDatasetRaw).filter_by(dataset_version_id=dataset_id).delete()

        # Пытаемся удалить версию и строки датасета каскадно
        db.delete(dataset)
        db.commit()

        return {
            "status": "deleted",
            "dataset_version_id": str(dataset_id),
            "rows_deleted": dataset.row_count
        }

    except Exception as e:
        db.rollback()

        # Проверяем, не из-за внешнего ключа ли ошибка
        if "foreign key" in str(e).lower() or "restrict" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail="Cannot delete dataset: it is used by one or more models"
            )

        # Другая ошибка
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )




# =========================================
# MODEL DEACTIVATE
# =========================================

@router.post("/models/{model_id}/deactivate")
def deactivate_model(
    model_id: int,
    db: Session = Depends(get_db),
):
    registry = ModelRegistryService(db)

    try:
        model = registry.deactivate_model(model_id)

        return {
            "status": "deactivated",
            "model_id": model.id,
            "name": model.name,
            "version": model.version,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))



# =========================================
# MODEL DETAILS
# =========================================

@router.get("/models/{model_id}")
def get_model_details(
    model_id: int,
    db: Session = Depends(get_db),
):
    stmt = select(MLModel).where(
        and_(
            MLModel.id == model_id,
            MLModel.is_deleted.is_(False),
        )
    )

    model = db.execute(stmt).scalar_one_or_none()

    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "id": model.id,
        "name": model.name,
        "version": model.version,
        "algorithm": model.algorithm,
        "model_type": model.model_type,
        "target": model.target,
        "dataset_version_id": str(model.dataset_version_id),
        "features": model.features,
        "metrics": model.metrics,
        "trained_rows_count": model.trained_rows_count,
        "model_path": model.model_path,
        "is_active": model.is_active,
        "trained_at": model.trained_at,
    }

# =========================================
# MODEL METRICS
# =========================================

@router.get("/models/{model_id}/metrics")
def get_model_metrics(
    model_id: int,
    db: Session = Depends(get_db),
):
    stmt = select(MLModel.metrics).where(
        and_(
            MLModel.id == model_id,
            MLModel.is_deleted.is_(False),
        )
    )

    metrics = db.execute(stmt).scalar_one_or_none()

    if metrics is None:
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "model_id": model_id,
        "metrics": metrics,
    }


# =========================================
# WHICH DATASET TEACHES MODEL
# =========================================


@router.get("/datasets/{dataset_version_id}/models")
def get_models_by_dataset(
    dataset_version_id: UUID,
    db: Session = Depends(get_db),
):

    stmt = (
        select(MLModel)
        .where(
            and_(
                MLModel.dataset_version_id == dataset_version_id,
                MLModel.is_deleted.is_(False),
            )
        )
        .order_by(MLModel.created_at.desc())
    )

    models = db.execute(stmt).scalars().all()

    return [
        {
            "id": m.id,
            "name": m.name,
            "version": m.version,
            "is_active": m.is_active,
            "trained_rows_count": m.trained_rows_count,
            "trained_at": m.trained_at,
        }
        for m in models
    ]

