# app/api/v1/ml/router.py


from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from pathlib import Path
import logging
import shutil
import tempfile
import zipfile
import json
import uuid

from uuid import UUID, uuid4

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, select, and_

from app.db.session import get_db
from models.activation_history import ModelActivationHistory
from models.ml_model import MLModel

from app.core.settings import settings

from app.ml.model_registry.promotion_policy import decide_promotion

from app.services.ml_training_service import MLTrainingService
from app.services.ml_prediction_service import MLPredictionService
from app.services.registry_service import ModelRegistryService
from app.services.dataset_service import DatasetService
from app.services.dataset_streaming_service import DatasetStreamingService
from app.services.audit_service import get_audit_page

from models.dataset_upload_history import DatasetUploadHistory
from models.industrial_dataset import IndustrialDatasetRaw
from sqlalchemy import cast, String

from app.ml.runtime_state import ML_RUNTIME_STATE
from app.schemas.dataset_schema_csv import (
    TrainRequest,
    TrainResponse,
)

from app.schemas.prediction_schema import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
)

from app.controllers.model_activation_controller import ModelActivationController
from app.controllers.models_compare_controller import ModelsCompareController
from app.controllers.model_evaluation_controller import ModelEvaluationController
from app.controllers.dataset_upload_controller import DatasetUploadController
from app.controllers.dataset_delete_controller import DatasetDeleteController





logger = logging.getLogger("promo_ml")

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
# AUDIT
# =========================================


@router.get("/audit")
def list_prediction_audit(
    page: int = 1,
    model_id: int | None = None,
    db: Session = Depends(get_db),
):

    return get_audit_page(db, page, model_id)



# =========================================
# MODEL Upload + Decision
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


@router.post("/train", response_model=TrainResponse)  # ← меняем response_model
def train_model(
        request: TrainRequest,
):
    """
    Обучает модель на ВСЁМ датасете (industrial_dataset_raw).
    Модель предсказывает k_uplift (коэффициент прироста продаж).
    Параметры:
    - promote: bool — автоматически активировать модель после обучения
    """
    logger.info(f"🔥 TRAIN REQUEST: {request}")
    logger.info(f"🔥 promote: {request.promote}")

    result = training_service.train(
        promote=request.promote,
        trigger="api",
    )

    return TrainResponse(**result)  # ← меняем на TrainResponse



# =========================================
# MODEL EVALUATE By Id
# =========================================

@router.post("/models/evaluate/{model_id}")
def evaluate_model(
        model_id: int,
        db: Session = Depends(get_db),
):
    controller = ModelEvaluationController()

    try:
        return controller.evaluate_model(model_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# MODEL ROLLBACK
# =========================================


@router.post("/models/rollback")
def rollback_model(
    db: Session = Depends(get_db)
):
    """
    Откатывает на предыдущую активную модель,
    используя таблицу истории активаций.
    """
    from models.activation_history import ModelActivationHistory

    # 1. Найти последние 2 активации
    last_two = db.query(ModelActivationHistory).order_by(
        ModelActivationHistory.activated_at.desc()
    ).limit(2).all()

    logger.info(f"📊 Last two: {[(h.id, h.model_id) for h in last_two]}")

    if len(last_two) < 2:
        raise HTTPException(
            status_code=400,
            detail="Not enough activation history for rollback"
        )

    current_activation, previous_activation = last_two[0], last_two[1]

    # 2. Получить модели
    current_model = db.get(MLModel, current_activation.model_id)
    previous_model = db.get(MLModel, previous_activation.model_id)

    if not current_model or not previous_model:
        raise HTTPException(status_code=404, detail="Models not found")

    logger.info(f"📦 Current model active: {current_model.is_active}, Previous model active: {previous_model.is_active}")

    # 3. Выполнить откат
    current_model.is_active = False
    previous_model.is_active = True

    # 4. Записать новую активацию в историю
    new_history = ModelActivationHistory(
        model_id=previous_model.id,
        activated_by="rollback"
    )
    db.add(new_history)

    db.commit()

    # 5. Обновить runtime
    from app.ml.runtime_state import ML_RUNTIME_STATE
    ML_RUNTIME_STATE["ml_model_id"] = previous_model.id
    ML_RUNTIME_STATE["model_loaded"] = False

    logger.info(f"✅ Rollback completed: {current_model.id} -> {previous_model.id}")

    return {
        "status": "rolled_back",
        "from_model_id": current_model.id,
        "to_model_id": previous_model.id,
        "rolled_back_at": new_history.activated_at.isoformat()
    }




# =========================================
# MODELS Activation History
# =========================================

@router.get("/models/activation-history")
def get_activation_history(
        limit: int = 10,
        db: Session = Depends(get_db)
):
    """
    Возвращает историю активаций моделей.
    """
    history = db.query(ModelActivationHistory).order_by(
        ModelActivationHistory.activated_at.desc()
    ).limit(limit).all()

    return [
        {
            "id": h.id,
            "model_id": h.model_id,
            "activated_at": h.activated_at.isoformat(),
            "activated_by": h.activated_by or "system"
        }
        for h in history
    ]


# =========================================
# MODEL LINEAGE
# =========================================

@router.get("/models/lineage")
def get_lineage():

    if not LINEAGE_FILE.exists():
        return []

    with open(LINEAGE_FILE) as f:
        return json.load(f)

# =========================================
# MODELS LIST
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
            "id": m.id,
            "ml_model_id": m.id,
            "name": m.name,
            "algorithm": m.algorithm,
            "version": m.version,
            "is_active": m.is_active,
            "trained_at": m.created_at,
            "created_at": m.created_at,  # ← для отладки
            "trained_rows_count": m.trained_rows_count,
            "features": m.features,
            "metrics": m.metrics,
            "active_in_runtime": m.id == active_model_id
        }
        for m in models
    ]


# =========================================
# MODEL Activate (Promote)
# =========================================

@router.post("/models/{model_id}/promote")
@router.post("/models/{model_id}/activate")
def promote_model(
    model_id: int,
    db: Session = Depends(get_db),
):
    controller = ModelActivationController()

    try:
        return controller.promote_model(model_id, db)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ========================================
# PREDICT (FastAPI)
# =======================================

from app.controllers.prediction_controller import PredictionController


@router.post(
    "/predict",
    summary="ML предсказание коэффициента прироста (k_uplift) + SHAP",
    response_model=PredictionResponse,
)
def predict(
    payload: PredictionRequest,
    svc: MLPredictionService = Depends(get_prediction_service),
    db: Session = Depends(get_db),
):
    controller = PredictionController(svc,db)
    return controller.predict(payload, db)


# ========================================
# PREDICT BATCH (множественный)
# ========================================

@router.post(
    "/predict/batch",
    summary="Batch ML предсказание",
    response_model=BatchPredictionResponse,
)
def predict_batch(
    payload: BatchPredictionRequest,
    svc: MLPredictionService = Depends(get_prediction_service),
    db: Session = Depends(get_db),
):
    """
    Принимает список запросов (до 100) и возвращает список прогнозов.
    """
    controller = PredictionController(svc, db)
    return controller.predict_batch(payload, db)



# =========================================
# MODEL DELETE
# =========================================

@router.delete("/models/{model_id}")
def delete_model(
        model_id: int,
        db: Session = Depends(get_db)
):
    """
    Полностью удаляет модель из БД и файловой системы.
    Даже если файлы отсутствуют, запись из БД удаляется.
    """
    # Находим модель
    model = db.get(MLModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Если модель активна — ошибка (нельзя удалить активную)
    if model.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete active model. Deactivate it first."
        )

    # ===== 1. УДАЛЯЕМ ФАЙЛЫ (ИГНОРИРУЕМ ОШИБКИ) =====
    file_deletion_errors = []
    model_file = None  # ← ИНИЦИАЛИЗИРУЕМ

    if model.model_path:
        try:
            model_path_str = str(model.model_path)
            model_file = Path(model_path_str)  # ← теперь точно определён

            # Удаляем файл модели
            if model_file.exists():
                model_file.unlink()
                logger.info(f"Deleted model file: {model_file}")
        except Exception as e:
            file_deletion_errors.append(f"Model file: {e}")
            logger.warning(f"Could not delete model file: {e}")

        # Удаляем meta.json (только если model_file определён)
        if model_file and model_file.exists():
            try:
                meta_file = model_file.with_suffix('.meta.json')
                if meta_file.exists():
                    meta_file.unlink()
                    logger.info(f"Deleted meta file: {meta_file}")
            except Exception as e:
                file_deletion_errors.append(f"Meta file: {e}")
                logger.warning(f"Could not delete meta file: {e}")

        # Удаляем shap-файлы (только если model_file определён)
        if model_file and model_file.exists():
            try:
                model_dir = model_file.parent
                for shap_file in model_dir.glob("shap_*"):
                    if shap_file.exists():
                        shap_file.unlink()
                        logger.info(f"Deleted shap file: {shap_file}")
            except Exception as e:
                file_deletion_errors.append(f"Shap files: {e}")
                logger.warning(f"Could not delete shap files: {e}")

    # ===== 2. УДАЛЯЕМ ИСТОРИЮ АКТИВАЦИЙ =====
    try:
        db.query(ModelActivationHistory).filter(
            ModelActivationHistory.model_id == model_id  # type: ignore
        ).delete(synchronize_session=False)
        logger.info(f"Deleted activation history for model {model_id}")
    except Exception as e:
        logger.warning(f"Could not delete activation history: {e}")

    # ===== 3. УДАЛЯЕМ ЗАПИСЬ ИЗ БД =====
    try:
        db.delete(model)
        db.commit()
        logger.info(f"Model {model_id} permanently deleted from database")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete model {model_id} from DB: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete model from database")

    # Формируем сообщение о результате
    message = "Model removed from database"
    if file_deletion_errors:
        message += f". Note: some files could not be deleted: {', '.join(file_deletion_errors)}"
    else:
        message += " and filesystem"

    return {
        "status": "deleted",
        "model_id": model_id,
        "message": message
    }

# =========================================
# DATASET STAT
# =========================================

@router.get("/dataset/stats")
def get_dataset_stats():
    """
    Возвращает статистику по единому датасету:
    - общее количество строк
    - история загрузок
    """
    service = DatasetService()
    return service.get_stats()


# =========================================
# DATASET UPLOAD CSV
# =========================================


@router.post("/dataset/upload")
def upload_dataset(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    Загружает CSV файл и добавляет данные в industrial_dataset_raw
    """
    logger.info(f"📤 Uploading dataset: {file.filename}")

    controller = DatasetUploadController(db)

    try:
        result = controller.upload_csv(file)
        return result
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# DATASET Batches List
# =========================================


@router.get("/dataset/batches")
def list_batches(db: Session = Depends(get_db)):
    """
    Возвращает список всех загрузок (batches)
    """
    batches = db.query(DatasetUploadHistory).order_by(
        DatasetUploadHistory.uploaded_at.desc()
    ).all()

    return [
        {
            "batch_id": str(b.batch_id),
            "uploaded_at": b.uploaded_at.isoformat(),
            "records_added": b.records_added,
            "status": b.status
        }
        for b in batches
    ]


# =========================================
# DATASET DELETE BY BATCH ID
# =========================================

@router.delete("/dataset/batch/{batch_id}")
def delete_dataset_batch(
        batch_id: UUID,
        force: bool = False,
        db: Session = Depends(get_db)
):
    """
    Удаляет все записи, загруженные в рамках указанного batch_id.
    """
    controller = DatasetDeleteController(db)
    return controller.delete_batch(batch_id, force)


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


#===================================
# Models Compare
#===================================

@router.get("/models/compare")
def compare_models(
    model_a: int,
    model_b: int,
    db: Session = Depends(get_db),
):
    controller = ModelsCompareController()

    try:
        return controller.compare_models(model_a, model_b, db)

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
        "features": model.features,
        "metrics": model.metrics,
        "trained_rows_count": model.trained_rows_count,
        "model_path": model.model_path,
        "is_active": model.is_active,
        "trained_at": model.created_at,  # ← используем created_at
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
# CLEANUP OLD MODELS
# =========================================


@router.post("/cleanup")
def cleanup_old_models(
        days: int = 2,
        db: Session = Depends(get_db)
):
    """
    Удаляет модели, помеченные как удалённые более N дней назад
    """
    from datetime import datetime, timedelta
    from sqlalchemy import and_

    cutoff = datetime.now() - timedelta(days=days)

    old_deleted = db.query(MLModel).filter(
        and_(
            MLModel.is_deleted == True,  # type: ignore
            MLModel.updated_at < cutoff  # type: ignore
        )
    ).all()

    count = 0
    for model in old_deleted:
        try:
            # Удаляем файлы
            if model.model_path:
                model_path_str = str(model.model_path)
                model_file = Path(model_path_str)
                if model_file.exists():
                    model_file.unlink()
            # Удаляем из БД
            db.delete(model)
            count += 1
        except Exception as e:
            logger.error(f"Failed to cleanup model {model.id}: {e}")

    db.commit()

    return {
        "status": "cleaned",
        "deleted_count": count
    }

# =========================================
# Dataset Upload Stream NDJSON
# =========================================

@router.post("/dataset/stream")
async def stream_dataset(
    request: Request,
    ml_service: MLPredictionService = Depends(),
    db: Session = Depends(get_db),
):
    """
    Streaming endpoint for dataset upload from 1C
    Accepts NDJSON (Newline Delimited JSON) stream
    Returns upload statistics after processing all data
    """
    logger.info("🔴 STREAM ENDPOINT CALLED")

    service = DatasetStreamingService(ml_service)

    # 🔥 Передаём db
    result = await service.process_stream(request.stream(), db)

    return result


# app/api/v1/ml/router.py

@router.get("/dataset/info")
def get_dataset_info(db: Session = Depends(get_db)):
    """
    Возвращает информацию о текущем датасете:
    - общее количество строк
    - история загрузок
    """
    total_rows = db.query(IndustrialDatasetRaw).count()

    uploads = db.query(DatasetUploadHistory).order_by(
        DatasetUploadHistory.uploaded_at.desc()
    ).limit(50).all()

    return {
        "total_rows": total_rows,
        "upload_history": [
            {
                "uploaded_at": h.uploaded_at.isoformat(),
                "records_added": h.records_added,
                "total_records_after": h.total_records_after,
                "status": h.status,
            }
            for h in uploads
        ]
    }


# ОТЛАДОЧНЫЙ ENDPOINT

@router.get("/dataset/batch/{batch_id}/debug")
def debug_batch(
        batch_id: str,
        db: Session = Depends(get_db)
):
    """
    Отладочный эндпоинт для проверки batch_id
    """
    from sqlalchemy import cast, String

    # Ищем в истории
    upload_record = db.query(DatasetUploadHistory).filter(
        cast(DatasetUploadHistory.batch_id, String) == batch_id
    ).first()

    # Ищем в данных
    rows_count = db.query(IndustrialDatasetRaw).filter(
        cast(IndustrialDatasetRaw.batch_id, String) == batch_id
    ).count()

    # Все batch_id из истории
    all_batches = db.query(DatasetUploadHistory.batch_id).all()
    all_batches_str = [str(b[0]) for b in all_batches]

    return {
        "search_batch_id": batch_id,
        "found_in_history": upload_record is not None,
        "rows_count_in_data": rows_count,
        "all_batches": all_batches_str[:10],  # первые 10
        "batch_exists": batch_id in all_batches_str
    }

# =====================================
# TRAINING METRICS CHART
# =====================================

@router.get("/training/metrics")
def get_training_metrics():
    """
    Возвращает метрики обучения для графика
    """
    import pandas as pd
    from pathlib import Path

    # Путь к файлу с метриками CatBoost
    catboost_info_dir = Path("catboost_info")
    learn_error_path = catboost_info_dir / "learn_error.tsv"

    if not learn_error_path.exists():
        return {
            "iterations": [],
            "rmse": [],
            "best_iteration": None,
            "message": "No training metrics available yet"
        }

    try:
        df = pd.read_csv(learn_error_path, sep="\t")

        # Находим лучшую итерацию
        best_idx = df["RMSE"].idxmin()

        return {
            "iterations": df["iter"].tolist(),
            "rmse": df["RMSE"].tolist(),
            "best_iteration": int(df["iter"].iloc[best_idx]),
            "best_rmse": float(df["RMSE"].iloc[best_idx]),
            "total_iterations": len(df)
        }
    except Exception as e:
        return {
            "iterations": [],
            "rmse": [],
            "best_iteration": None,
            "error": str(e)
        }
