# app/api/v1/ml/router.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from pathlib import Path
import logging
import shutil
import tempfile
import zipfile
import json
import uuid
from io import BytesIO
from uuid import UUID, uuid4
import pandas as pd
from typing import Union, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text, select, delete, and_

from app.db.session import get_db
from app.ml.train.train_pipeline import load_dataset_by_version
from models.activation_history import ModelActivationHistory
from models.ml_model import MLModel

from app.core.settings import settings

from app.ml.model_registry.promotion_policy import decide_promotion

from app.services.ml_training_service import MLTrainingService
from app.services.ml_prediction_service import MLPredictionService
from app.ml.registry.service import ModelRegistryService


from models.dataset_version import DatasetVersion
from models.industrial_dataset import IndustrialDatasetRaw
from app.ml.contract_check import validate_industrial_contract

from app.ml.predictor import Predictor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

from app.ml.runtime_state import ML_RUNTIME_STATE
from app.schemas.dataset_schema import (
    DatasetVersionResponse,
    TrainRequest,
    TrainOnAllResponse,
    TrainSingleResponse,
)
from app.services.dataset_service import DatasetService

from app.api.v1.ml.schemas import (
    PredictionRequest,
    PredictionResponse,
    OneCPredictRequest,
    OneCPredictResponse,
    ShapValue,
)

from app.services.audit_service import get_audit_page


logger = logging.getLogger(__name__)

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




@router.post("/train", response_model=Union[TrainOnAllResponse, TrainSingleResponse])
def train_model(
        request: TrainRequest,
        # db: Session = Depends(get_db)
):
    """
    Обучает модель на одном или всех датасетах.

    - Если train_on_all=True: обучает на всех доступных датасетах
    - Если train_on_all=False: обучает на конкретном dataset_version_id
    """

    logger.info(f"🔥 RAW TRAIN REQUEST: {request}")
    logger.info(f"🔥 REQUEST DICT: {request.model_dump()}")
    logger.info(f"🔥 train_on_all: {request.train_on_all}")
    logger.info(f"🔥 dataset_version_id: {request.dataset_version_id}")
    logger.info(f"🔥 promote: {request.promote}")

    if request.train_on_all:
        result = training_service.train_on_all_datasets(
            promote=request.promote,
            trigger="api"
        )
        return TrainOnAllResponse(**result)
    else:
        if not request.dataset_version_id:
            raise HTTPException(400, "dataset_version_id required")

        result = training_service.train(
            dataset_version_id=request.dataset_version_id,
            promote=request.promote,
            trigger="api",
        )

        return TrainSingleResponse(**result)



# =========================================
# MODEL EVALUATE By Id
# =========================================

@router.post("/models/evaluate/{model_id}")
def evaluate_model(
        model_id: int,
        dataset_version_id: Optional[UUID] = None,
        db: Session = Depends(get_db)
):
    """
    Оценивает качество модели на указанном датасете.
    Если dataset_version_id не указан, использует датасет, на котором модель обучалась.
    """


    # 1. Найти модель в БД
    model_record = db.get(MLModel, model_id)
    if not model_record or model_record.is_deleted:
        raise HTTPException(status_code=404, detail="Model not found")

    # 2. Определить датасет для оценки
    eval_dataset_id = dataset_version_id or model_record.dataset_version_id
    if not eval_dataset_id:
        raise HTTPException(
            status_code=400,
            detail="No dataset specified for evaluation and model has no training dataset"
        )

    # 3. Загрузить данные
    try:
        df = load_dataset_by_version(db, eval_dataset_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dataset: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="Dataset is empty")

    # 4. Проверить наличие целевой колонки
    target = model_record.target
    if target not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Target column '{target}' not found in dataset"
        )

    # 5. Проверить наличие всех фич
    features = [f for f in model_record.features]  # ← явное преобразование
    missing = set(features) - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing features in evaluation dataset: {missing}"
        )

    # 6. Подготовить данные
    X = df[features]
    y_true = df[target]

    # 7. Проверить на NaN
    if X.isnull().any().any():
        null_counts = X.isnull().sum()
        null_cols = [col for col in features if null_counts[col] > 0]
        logger.warning(f"NaN values found in evaluation data: {null_counts}")

        # Удаляем строки с NaN (или можно выдать ошибку)
        X_clean = X.dropna()
        y_clean = y_true[X_clean.index]

        if len(X_clean) == 0:
            raise HTTPException(
                status_code=400,
                detail="All rows contain NaN values after cleaning"
            )

        logger.info(f"Removed {len(X) - len(X_clean)} rows with NaN values")
        X, y_true = X_clean, y_clean

    # 8. Загрузить модель через Predictor
    predictor = Predictor()
    # noinspection PyTypeChecker
    if not predictor.load_by_id(model_record):  # type: ignore
        raise HTTPException(status_code=500, detail="Failed to load model file")

    # 9. Сделать предсказания
    try:
        y_pred = predictor.predict(X, collect_metrics=False)  # ← вызываем метод predict у predictor
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    # 10. Рассчитать метрики
    rmse = float(mean_squared_error(y_true, y_pred, squared=False))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))

    # Дополнительные метрики
    mape = float(np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100)

    metrics = {
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "r2": round(r2, 4),
        "mape": round(mape, 2)
    }

    # 11. Записать в lineage
    record_lineage_event(
        "evaluate",
        str(model_id),
        {
            "dataset_version_id": str(eval_dataset_id),
            "metrics": metrics,
            "rows_evaluated": len(y_true)
        }
    )

    logger.info(f"Model {model_id} evaluated on dataset {eval_dataset_id}: {metrics}")

    return {
        "model_id": model_id,
        "dataset_version_id": str(eval_dataset_id),
        "rows_evaluated": len(y_true),
        "metrics": metrics
    }


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


# @router.post("/models/rollback/{model_id}")
# def rollback_model(
#     model_id: int,
#     db: Session = Depends(get_db)
# ):
#     """
#     Откатывает production-модель на предыдущую активную версию.
#     Работает через БД, без копирования файлов.
#     """
#     # 1. Найти модель для отката
#     target_model = db.get(MLModel, model_id)
#     if not target_model or target_model.is_deleted:
#         raise HTTPException(status_code=404, detail="Model not found")
#
#     # 2. Найти текущую активную модель
#     current_active = db.query(MLModel).filter(
#         MLModel.name == target_model.name,
#         MLModel.is_active == True,
#         MLModel.is_deleted == False
#     ).first()
#
#     if not current_active:
#         raise HTTPException(status_code=400, detail="No active model found")
#
#     # 3. Найти предыдущую активную модель
#     # Берём две последние модели (по trained_at)
#     recent_models = (
#         db.query(MLModel)
#         .filter(
#             MLModel.name == target_model.name,
#             MLModel.is_deleted == False
#         )
#         .order_by(MLModel.trained_at.desc())
#         .limit(2)
#         .all()
#     )
#
#     if len(recent_models) < 2:
#         raise HTTPException(
#             status_code=400,
#             detail="Not enough models in history for rollback"
#         )
#
#     current, previous = recent_models[0], recent_models[1]
#
#     # 4. Если запрошен не тот откат — проверим
#     if target_model.id != current.id and target_model.id != previous.id:
#         raise HTTPException(
#             status_code=400,
#             detail="Can only rollback to the immediately previous model"
#         )
#
#     # 5. Выполнить откат
#     current.is_active = False
#     previous.is_active = True
#
#     db.commit()
#
#     # 6. Обновить runtime state (если используется)
#     from app.ml.runtime_state import ML_RUNTIME_STATE
#     ML_RUNTIME_STATE["ml_model_id"] = previous.id
#     ML_RUNTIME_STATE["model_loaded"] = False  # принудительно перезагрузить
#
#     # 7. Записать в lineage
#     record_lineage_event(
#         "rollback",
#         str(model_id),
#         {
#             "rolled_back_to": previous.id,
#             "previous_active": current.id,
#             "model_name": current.name
#         }
#     )
#
#     logger.info(f"Rollback completed: model {current.id} -> {previous.id}")
#
#     return {
#         "status": "rolled_back",
#         "previous_active_model_id": current.id,
#         "new_active_model_id": previous.id,
#         "message": f"Rolled back from model {current.id} to {previous.id}"
#     }

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
            "ml_model_id": m.id,
            "name": m.name,
            "algorithm": m.algorithm,
            "version": m.version,
            "dataset_version_id": str(m.dataset_version_id) if m.dataset_version_id else None,  # ← может быть null
            "trained_on_all": m.dataset_version_id is None,  # ← флаг для UI
            "is_active": m.is_active,
            "trained_at": m.trained_at,
            "created_at": m.created_at,
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
    registry = ModelRegistryService(db)

    try:
        model = registry.promote_model(model_id)  # ← здесь уже commit

        # ✅ Обновляем runtime state
        ML_RUNTIME_STATE["ml_model_id"] = model.id
        ML_RUNTIME_STATE["version"] = model.version
        ML_RUNTIME_STATE["feature_order"] = model.features
        ML_RUNTIME_STATE["model_path"] = model.model_path  # ← добавляем путь!
        ML_RUNTIME_STATE["model_loaded"] = False

        # ✅ Просто добавляем запись, НЕ коммитим
        history_entry = ModelActivationHistory(
            model_id=model.id,
            activated_by="user"
        )
        db.add(history_entry)


        # Всё закоммитится автоматически при закрытии сессии
        # или можно сделать ещё один commit, но не обязательно

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
    db: Session = Depends(get_db),
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

    # 🔥 ВАЖНО: получаем model_id и model_version из runtime state
    model_id = ML_RUNTIME_STATE.get("ml_model_id")
    model_version = ML_RUNTIME_STATE.get("version")

    # Формируем response
    response = PredictionResponse(
        promo_code=payload.promo_code,
        sku=payload.sku,
        date=payload.prediction_date,
        prediction=prediction_result["prediction"],
        baseline=prediction_result["baseline"],
        uplift=prediction_result["uplift"],
        shap_values=shap_objs,
        ml_model_id=ML_RUNTIME_STATE["ml_model_id"],
        version=ML_RUNTIME_STATE["version"],
        trained_at=ML_RUNTIME_STATE.get("trained_at"),
        features=input_data,
        fallback_used=prediction_result["fallback_used"],
        reason=prediction_result["reason"],
    )

    # Сохраняем в аудит
    request_id = uuid4()

    # 🔥 КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: используем model_dump() с default=str
    features_json = json.dumps(payload.model_dump(), default=str)

    db.execute(
        text("""
            INSERT INTO ml_prediction_audit
            (
                request_id,
                model_id,
                model_version,
                prediction_value,
                features
            )
            VALUES
            (
                :request_id,
                :model_id,
                :model_version,
                :prediction_value,
                CAST(:features AS JSONB)
            )
        """),
        {
            "request_id": request_id,
            "model_id": model_id,
            "model_version": model_version,
            "prediction_value": prediction_result["prediction"],
            "features": features_json,  # ← используем подготовленный JSON
        }
    )

    db.commit()

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
# Параметр ml_model_id - это строка, имя файла модели (без .cbm)
# Например: "cb_promo_v1", "model_20260306_123456"

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

    logger.info(f"Model {ml_model_id} activated")

    return {
        "status": "activated",
        "ml_model_id": ml_model_id
    }


# =========================================
# MODEL DELETE
# =========================================

@router.delete("/models/{model_id}")
def delete_model(
        model_id: int,
        db: Session = Depends(get_db)
):
    """
    Удаляет модель (soft delete или hard delete).
    """
    model = db.get(MLModel, model_id)

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Вариант 1: Hard delete (полное удаление)
    # db.delete(model)

    # Вариант 2: Soft delete (рекомендуется)
    model.is_deleted = True
    model.is_active = False

    db.commit()

    logger.info(f"Model {model_id} deleted")

    return {
        "status": "deleted",
        "model_id": model_id
    }


# =========================================
# DATASET LIST
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

    # ========== ВАЖНО: КОНВЕРТИРУЕМ NaN В None ==========

    # Создаем новый DataFrame без NaN
    data_for_db = []
    for _, row in df.iterrows():
        clean_row = {}
        for col_name, value in row.items():
            if pd.isna(value):
                clean_row[col_name] = None
            elif isinstance(value, float) and str(value).lower() == 'nan':
                clean_row[col_name] = None
            else:
                clean_row[col_name] = value
        data_for_db.append(clean_row)

    # Преобразуем обратно в DataFrame для валидации
    df_clean = pd.DataFrame(data_for_db)

    # ========== ТЕКСТОВЫЕ ПОЛЯ: NULL -> "" ==========
    text_columns = [
        "PromoID", "SKU", "SKU_Level2", "SKU_Level3", "SKU_Level4", "SKU_Level5",
        "Category", "Supplier", "Region", "StoreID", "Store_Location_Type",
        "PromoMechanics", "PreviousPromoID", "PromoStatus", "MarketingCarrier",
        "MarketingMaterial", "FormatAssortment"
    ]

    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna("")
    # =================================================

    # ==========  Числовые поля: NULL -> 0  ==========
    numeric_columns = [
        "RegularPrice", "PromoPrice", "PurchasePriceBefore", "PurchasePricePromo",
        "PercentPriceDrop", "VolumeRegular", "HistoricalSalesPromo",
        "SalesQty_Promo", "SalesQty_PrevModel", "FM_Regular", "FM_Promo",
        "TurnoverBefore", "TurnoverPromo", "SeasonCoef_Week"
    ]

    for col in numeric_columns:
        if col in df_clean.columns:
            # Конвертируем в числа
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
            # Заменяем NaN на None (который станет NULL в БД)
            df_clean[col] = df_clean[col].where(pd.notnull(df_clean[col]), None)



    # ====================================================

    # Валидация датасета
    validate_industrial_contract(df_clean)

    # Создаём версию датасета
    dataset_version = DatasetVersion(
        id=uuid.uuid4(),
        row_count=len(df),
        status="READY"
    )
    db.add(dataset_version)
    db.flush()

    # Запись всех строк в raw таблицу
    records = df_clean.to_dict(orient="records")

    for row in records:
        # Создаем чистую копию строки без NaN
        clean_row = {}
        for key, value in row.items():
            # Если это float и это NaN - заменяем на None
            if isinstance(value, float) and value != value:  # NaN != NaN
                clean_row[key] = None
            else:
                clean_row[key] = value

        db_row = IndustrialDatasetRaw(
            dataset_version_id=dataset_version.id,
            **clean_row
        )
        db.add(db_row)

    db.commit()

    return {
        "dataset_version": str(dataset_version.id),
        "rows_loaded": len(df_clean),
        "detected_encoding": detected_encoding
    }


# =========================================
# DATASET DELETE (С ИГНОРИРОВАНИЕМ ЛИНТЕРА)
# =========================================

@router.delete("/datasets/{dataset_id}")
def delete_dataset(
        dataset_id: UUID,
        force: bool = False,
        db: Session = Depends(get_db)
):
    # Находим версию датасета
    dataset = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_id).first()  # type: ignore

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    from models.ml_model import MLModel

    # Преобразуем UUID в строку один раз
    ds_id_str = str(dataset_id)

    # ========== 1. ПРОВЕРЯЕМ СВЯЗАННЫЕ МОДЕЛИ ==========
    # Считаем модели, использующие этот датасет
    models_count = db.query(MLModel).filter(
        MLModel.dataset_version_id == ds_id_str  # type: ignore
    ).count()

    if models_count > 0 and not force:
        # Считаем активные модели
        active_models = db.query(MLModel).filter(
            MLModel.dataset_version_id == ds_id_str,  # type: ignore
            MLModel.is_deleted == False  # type: ignore
        ).count()

        raise HTTPException(
            status_code=409,
            detail={
                "message": "Cannot delete dataset: it is used by one or more models",
                "total_models": models_count,
                "active_models": active_models,
                "dataset_id": ds_id_str,
                "suggestion": "Use force=true to delete dataset and all related models"
            }
        )

    # ========== 2. ЕСЛИ force=True, УДАЛЯЕМ ВСЁ ==========
    try:
        # 2.1 Сначала удаляем все строки из industrial_dataset_raw
        raw_deleted = db.query(IndustrialDatasetRaw).filter(
            IndustrialDatasetRaw.dataset_version_id == ds_id_str  # type: ignore
        ).delete(synchronize_session=False)

        # 2.2 Если force=True, удаляем связанные модели
        if force and models_count > 0:
            models_deleted = db.query(MLModel).filter(
                MLModel.dataset_version_id == ds_id_str  # type: ignore
            ).delete(synchronize_session=False)
            logger.info(f"🗑️ Deleted {models_deleted} related models")

        # 2.3 Удаляем сам датасет
        db.delete(dataset)


        db.commit()

        return {
            "status": "deleted",
            "dataset_version_id": ds_id_str,
            "rows_deleted": raw_deleted,
            "models_deleted": models_count if force else 0,
            "force": force
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error deleting dataset {dataset_id}: {str(e)}")
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
    """
    Возвращает модели, обученные на конкретном датасете.
    Для моделей, обученных на всех датасетах, dataset_version_id = null
    """

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
            "trained_on_all": m.dataset_version_id is None,  # ← флаг для UI
        }
        for m in models
    ]

