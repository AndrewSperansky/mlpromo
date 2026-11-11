# app/api/v1/ml_torch/router.py

import json
import logging
from datetime import date, timedelta, datetime, timezone
from typing import List
from app.core.settings import settings
from fastapi import APIRouter, Depends, HTTPException, Request
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.ml_torch.train.train_pipeline import train_lstm_pipeline
from app.services.price_history_service import PriceHistoryService
from app.services.average_cheque_service import AverageChequeService
from app.services.sales_fact_service import SalesFactService
from app.services.exchange_rate_service import ExchangeRateService
from app.services.calendar_service import CalendarService
from app.ml_torch.inference.predictor import TorchPredictor
from app.services.registry_service import ModelRegistryService
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.ml.runtime_state import ML_RUNTIME_STATE

from app.schemas.torch_schema import (
    TrainLSTMRequest,
    PredictLSTMRequest,
    PredictLSTMResponse,
    AverageChequePushRequest,
    ExchangeRatePushRequest,
    CalendarPushRequest,
    RetailPricePushRequest,
    TrainLSTMUnifiedRequest,
)


router = APIRouter(tags=["ml_torch"])
logger = logging.getLogger("promo_ml")

@router.get("/health")
def health():
    return {"status": "ok", "module": "ml_torch"}


@router.get("/price-history/retail/{sku}")
def get_retail_price_history(
    sku: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    service = PriceHistoryService(db)
    history = service.get_retail_price_history(sku, days)
    return {"sku": sku, "days": days, "history": history}

# ============================================================
# ОБУЧЕНИЕ МОДЕЛИ
# ============================================================

@router.post("/train/lstm")
def train_lstm(
        request: TrainLSTMRequest,
        # db: Session = Depends(get_db),
        # current_user: User = Depends(get_current_user)
):
    """
    Обучает LSTM модель для прогнозирования цен на основе истории.

    Требует наличия данных в таблице retail_price_history. !!!!!!!
    """
    try:
        result = train_lstm_pipeline(
            sku=request.sku,
            days=request.days,
            seq_len=request.seq_len,
            hidden_size=request.hidden_size,
            num_layers=request.num_layers,
            learning_rate=request.learning_rate,
            batch_size=request.batch_size,
            epochs=request.epochs,
            promote=request.promote,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# app/api/v1/ml_torch/router.py

@router.post("/train/lstm/unified", summary="Обучение единой LSTM модели для всех SKU")
async def train_lstm_unified(
        request: TrainLSTMUnifiedRequest,
        # db: Session = Depends(get_db),
        # current_user: User = Depends(get_current_user)
):
    """
    Обучает одну модель для прогнозирования продаж любых SKU.
    Вход: исторические продажи всех SKU.
    Выход: единая модель с эмбеддингами SKU.
    """
    from app.ml_torch.train.train_pipeline import train_lstm_unified

    result = train_lstm_unified(
        days=request.days,
        seq_len=request.seq_len,
        hidden_size=request.hidden_size,
        num_layers=request.num_layers,
        embedding_dim=request.embedding_dim,
        learning_rate=request.learning_rate,
        batch_size=request.batch_size,
        epochs=request.epochs,
        promote=request.promote
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result




# ============================================================
# ПРОГНОЗ
# ============================================================

# app/api/v1/ml_torch/router.py

@router.post("/predict/lstm", response_model=PredictLSTMResponse)
def predict_lstm(
        request: PredictLSTMRequest,
        db: Session = Depends(get_db),
        # current_user: User = Depends(get_current_user)
):
    """
    Прогнозирует продажи с использованием активной LSTM модели.

    Для работы требуется:
    1. Активная LSTM модель в реестре (algorithm='pytorch_lstm' или 'pytorch_lstm_with_embeddings')
    2. История продаж SKU в таблице sales_fact
    """
    # ===== 1. НАХОДИМ АКТИВНУЮ LSTM МОДЕЛЬ =====
    registry = ModelRegistryService(db)

    active_models = registry.list_models()
    lstm_model = None
    for m in active_models:
        if m.algorithm in ["pytorch_lstm", "pytorch_lstm_with_embeddings"] and m.is_active:
            lstm_model = m
            break

    if not lstm_model:
        raise HTTPException(
            status_code=404,
            detail="Нет активной LSTM модели. Сначала обучите и активируйте модель."
        )

    # ===== 2. ЗАГРУЖАЕМ КОНФИГУРАЦИЮ ИЗ META.JSON =====
    meta_path = Path(lstm_model.model_path).with_suffix('.meta.json')
    if not meta_path.exists():
        candidate_dir = Path(settings.ML_CANDIDATE_DIR)
        meta_path = candidate_dir / f"{lstm_model.id}.meta.json"

    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
            model_config = meta.get("model_config", {})

            if "categorical_dims" not in model_config:
                model_config["categorical_dims"] = {}
            if "numeric_features" not in model_config:
                model_config["numeric_features"] = len(meta.get("numeric_features", []))

            logger.info(f"📋 Loaded config from meta: {model_config}")
    else:
        model_config = {
            "numeric_features": 7,
            "categorical_dims": {},
            "embedding_dim": 16,
            "hidden_size": 64,
            "num_layers": 2,
            "seq_len": 30
        }

    # ===== 3. ЗАГРУЖАЕМ МОДЕЛЬ =====
    predictor = TorchPredictor(db)
    predictor.load_model(Path(lstm_model.model_path), model_config)

    # ===== 4. ДЕЛАЕМ ПРОГНОЗ =====
    from datetime import date, timedelta

    predictions = []
    for i in range(request.days_ahead):
        forecast_date = date.today() + timedelta(days=i)

        try:
            result = predictor.predict_for_day(
                sku=request.sku,
                date=forecast_date,
                store_id=request.store_id if hasattr(request, 'store_id') else None
            )
            predictions.append({
                "date": forecast_date.isoformat(),
                "predicted_sales": result["predicted_quantity"]
            })
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ===== 5. ВОЗВРАЩАЕМ ОТВЕТ =====
    return PredictLSTMResponse(
        sku=request.sku,
        days_ahead=request.days_ahead,
        predictions=predictions,
        model_id=lstm_model.id
    )

# ============================================================
# Pull запрос на http сервис 1С для скачивания среднего чека
# ============================================================
@router.post("/sync/average-cheque")
async def sync_average_cheque(
        start_date: str,
        end_date: str,
        db: Session = Depends(get_db),
        # current_user: User = Depends(get_current_user)
):
    """
    Синхронизирует данные о среднем чеке из 1С.

    Для каждого магазина:
    - количество чеков
    - общая сумма
    - средний чек

    Плюс итоговая строка "Общий средний чек"
    """
    service = AverageChequeService()

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    result = await service.sync_from_1c(db, start, end)

    return result

# ================================================
# POST запрос от 1С для приема среднего чека
# ================================================

@router.post("/push/average-cheque")
async def push_average_cheque(
        request: AverageChequePushRequest,
        db: Session = Depends(get_db),
        # Временно без авторизации для теста
):
    """
    PUSH-приём данных о среднем чеке из 1С.
    """
    # Pydantic V2: используем model_dump() вместо dict()
    records = [r.model_dump() for r in request.records]

    service = AverageChequeService()
    result = await service.process_push_data(db, records)

    return result

# ================================================
# POST запрос от 1С ПРОДАЖИ
# ================================================

@router.post("/push/sales-fact")
async def push_sales_fact(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    data = json.loads(body)
    records = data.get("records", [])

    service = SalesFactService()
    result = await service.process_push_data(db, records)
    return result

# ================================================
# POST запрос от 1С КУРСЫ ВАЛЮТ
# ================================================

@router.post("/push/exchange-rates")
async def push_exchange_rates(
    request: ExchangeRatePushRequest,
    db: Session = Depends(get_db),
):
    service = ExchangeRateService()
    result = await service.process_push_data(db, request.records)
    return result


# ================================================
# POST запрос от 1С КАЛЕНДАРЬ
# ================================================


@router.post("/push/calendar")
async def push_calendar(
        request: CalendarPushRequest,
        db: Session = Depends(get_db),
):
    """
    PUSH-приём данных производственного календаря из 1С.

    Ожидает записи с полями:
    - date: дата
    - day_type: тип дня (Праздник, Суббота, Воскресенье, Рабочий, Предпраздничный)
    - week: номер недели в году
    - year: год
    """
    service = CalendarService()
    result = await service.process_push_data(db, request.records)
    return result


# ============================================================
# PUSH запросы для загрузки цен
# ============================================================

@router.post("/push/retail-prices")
async def push_retail_prices(
    request: RetailPricePushRequest,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    from app.services.price_history_service import PriceHistoryService
    service = PriceHistoryService(db)
    # 🔥 Преобразуем Pydantic модели в dict
    records = [r.model_dump() for r in request.records]
    result = await service.process_retail_prices(db, records)
    return result


# @router.post("/push/purchase-prices")
# async def push_purchase_prices(
#     request: PurchasePricePushRequest,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     from app.services.price_history_service import PriceHistoryService
#     service = PriceHistoryService(db)
#     # 🔥 Преобразуем Pydantic модели в dict
#     records = [r.model_dump() for r in request.records]
#     result = await service.process_purchase_prices(db, records)
#     return result




# ================================================
# Эндпоинт для обучения LSTM
# ================================================


@router.post("/train/lstm")
async def train_lstm(
        request: TrainLSTMRequest,
        db: Session = Depends(get_db),
        # current_user: User = Depends(get_current_user)
):
    """
    Обучает LSTM модель для прогнозирования цен на основе истории.
    """
    from app.ml_torch.train.train_pipeline import train_lstm_pipeline

    result = train_lstm_pipeline(
        sku=request.sku,
        days=request.days,
        seq_len=request.seq_len,
        hidden_size=request.hidden_size,
        num_layers=request.num_layers,
        learning_rate=request.learning_rate,
        batch_size=request.batch_size,
        epochs=request.epochs,
        promote=request.promote
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result



# ================================================================
# 🔮 LSTM HITL (Human-In-The-Loop) Endpoints
# Функция "На будущее" и пока не используется,
# ================================================================

@router.get("/compare/catboost")
def compare_lstm_catboost(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    Сравнивает активную LSTM модель с CatBoost.
    Возвращает метрики обеих моделей для HITL.

    FOR COMING FUTURE: Используется для принятия решения об активации LSTM.
    """
    from app.services.registry_service import ModelRegistryService

    registry = ModelRegistryService(db)

    # Получаем активную LSTM модель
    lstm_model = registry.get_active_model_by_algorithm("pytorch_lstm_with_embeddings")

    # Получаем активную CatBoost модель
    catboost_model = registry.get_active_model_by_algorithm("catboost")

    # ===== Базовый ответ =====
    result = {
        "lstm": {
            "id": lstm_model.id if lstm_model else None,
            "version": lstm_model.version if lstm_model else None,
            "metrics": lstm_model.metrics if lstm_model else None,
            "is_active": lstm_model.is_active if lstm_model else False,
            "is_trained": lstm_model is not None,
            "exists": lstm_model is not None,
        },
        "catboost": {
            "id": catboost_model.id if catboost_model else None,
            "version": catboost_model.version if catboost_model else None,
            "metrics": catboost_model.metrics if catboost_model else None,
            "is_active": catboost_model.is_active if catboost_model else True,
            "exists": catboost_model is not None,
        },
        "comparison": None,
        "lstm_active_in_runtime": ML_RUNTIME_STATE.get("lstm_active", False),
    }

    # ===== Сравниваем метрики, если обе модели есть =====
    if lstm_model and catboost_model:
        lstm_metrics = lstm_model.metrics or {}
        catboost_metrics = catboost_model.metrics or {}

        # Извлекаем RMSE
        lstm_rmse = lstm_metrics.get("rmse") or lstm_metrics.get("val_loss")
        catboost_rmse = catboost_metrics.get("rmse")

        # Извлекаем Coverage
        lstm_coverage = lstm_metrics.get("coverage")
        catboost_coverage = catboost_metrics.get("coverage")

        # Извлекаем Uplift
        lstm_uplift = lstm_metrics.get("uplift")
        catboost_uplift = catboost_metrics.get("uplift")

        comparison = {
            "rmse": {
                "lstm": lstm_rmse,
                "catboost": catboost_rmse,
                "diff": round(lstm_rmse - catboost_rmse, 6) if lstm_rmse and catboost_rmse else None,
                "is_better": lstm_rmse < catboost_rmse if lstm_rmse and catboost_rmse else None,
            },
            "coverage": {
                "lstm": lstm_coverage,
                "catboost": catboost_coverage,
                "is_better": lstm_coverage > catboost_coverage if lstm_coverage and catboost_coverage else None,
            },
            "uplift": {
                "lstm": lstm_uplift,
                "catboost": catboost_uplift,
                "is_better": lstm_uplift > catboost_uplift if lstm_uplift and catboost_uplift else None,
            }
        }

        # Вычисляем общую оценку
        if lstm_rmse and catboost_rmse:
            improvement_percent = ((catboost_rmse - lstm_rmse) / catboost_rmse) * 100 if catboost_rmse != 0 else 0
            comparison["overall"] = {
                "improvement_percent": round(improvement_percent, 2),
                "is_better": lstm_rmse < catboost_rmse,
                "verdict": "LSTM is better" if lstm_rmse < catboost_rmse else "CatBoost is better",
                "recommendation": "Activate LSTM" if lstm_rmse < catboost_rmse else "Keep CatBoost",
            }

        result["comparison"] = comparison

    # ===== Если нет LSTM модели =====
    elif not lstm_model and catboost_model:
        result["message"] = "No LSTM model found. Train LSTM model first."      # type: ignore

    # ===== Если нет CatBoost модели =====
    elif lstm_model and not catboost_model:
        result["message"] = "No CatBoost model found. Train CatBoost model first."      # type: ignore

    # ===== Если нет ни одной модели =====
    else:
        result["message"] = "No models found. Train models first."          # type: ignore

    return result



# ================================================================
# 🔮 LSTM HITL (Human-In-The-Loop) — простой статус + активация
# ================================================================

@router.get("/status")
def get_lstm_status(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    Возвращает статус LSTM модели и CatBoost для справки.
    """
    from app.services.registry_service import ModelRegistryService

    registry = ModelRegistryService(db)

    # Получаем активную LSTM модель (pytorch_lstm_with_embeddings)
    lstm_model = registry.get_active_model_by_algorithm("pytorch_lstm_with_embeddings")

    # Получаем активную CatBoost модель (для справки)
    catboost_model = registry.get_active_model_by_algorithm("catboost")

    # Проверяем, есть ли LSTM модели в принципе (не только активные)
    all_lstm_models = registry.get_models_by_algorithm("pytorch_lstm_with_embeddings", limit=1)

    return {
        "lstm": {
            "exists": lstm_model is not None,
            "has_candidate": len(all_lstm_models) > 0,
            "id": lstm_model.id if lstm_model else None,
            "version": lstm_model.version if lstm_model else None,
            "metrics": lstm_model.metrics if lstm_model else None,
            "is_active": ML_RUNTIME_STATE.get("lstm_active", False),
            "activated_at": ML_RUNTIME_STATE.get("lstm_activated_at"),
        },
        "catboost": {
            "id": catboost_model.id if catboost_model else None,
            "version": catboost_model.version if catboost_model else None,
            "metrics": catboost_model.metrics if catboost_model else None,
            "is_active": catboost_model.is_active if catboost_model else False,
        }
    }


@router.post("/activate")
def activate_lstm(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    Активирует LSTM модель как источник baseline.
    HITL: человек подтверждает активацию после сравнения.

    🔮 FUTURE: после обучения LSTM модели, эта функция
    будет делать её активной для всех прогнозов.

    СЕЙЧАС: если USE_LSTM=True — выполняет активацию,
    если USE_LSTM=False — возвращает сообщение о настройке.
    """
    from app.core.settings import settings
    from app.services.registry_service import ModelRegistryService
    from app.services.activity_service import ActivityService

    # ═══════════════════════════════════════════════════════════════
    # 🔮 LSTM INTEGRATION (FUTURE)
    # ═══════════════════════════════════════════════════════════════
    #
    # Сейчас LSTM выключена (USE_LSTM=False). Для включения:
    # 1. Обучите LSTM модель через /ml/torch/train/lstm/unified
    # 2. Установите USE_LSTM=True в настройках
    # 3. Используйте этот эндпоинт для активации
    # ═══════════════════════════════════════════════════════════════

    # Если LSTM выключена — возвращаем сообщение
    if not settings.USE_LSTM:
        return {
            "status": "not_implemented",
            "message": "LSTM activation is not yet available in production. "
                       "Please set USE_LSTM=True in settings when ready.",
            "docs": "See app/core/settings.py -> USE_LSTM"
        }

    logger.info("🔮 Attempting to activate LSTM model as baseline source")

    registry = ModelRegistryService(db)

    # Ищем LSTM модель
    lstm_model = registry.get_active_model_by_algorithm("pytorch_lstm_with_embeddings")

    if not lstm_model:
        raise HTTPException(
            status_code=404,
            detail="No LSTM model found. Train LSTM model first via /ml/torch/train/lstm/unified"
        )

    # Проверяем, не активна ли уже
    if ML_RUNTIME_STATE.get("lstm_active", False):
        raise HTTPException(
            status_code=400,
            detail="LSTM is already active. Deactivate first if you want to switch."
        )

    # Активируем LSTM в runtime_state
    ML_RUNTIME_STATE["lstm_active"] = True
    ML_RUNTIME_STATE["lstm_model_id"] = lstm_model.id
    ML_RUNTIME_STATE["lstm_activated_at"] = datetime.now(timezone.utc).isoformat()

    # Логируем действие
    ActivityService.log(
        db=db,
        user_id=current_user.id,
        action="activate_lstm",
        resource=f"lstm_model_{lstm_model.id}",
        details=f"LSTM model {lstm_model.id} (version {lstm_model.version}) activated as baseline source"
    )

    logger.info(f"✅ LSTM model {lstm_model.id} activated by user {current_user.username}")

    return {
        "status": "activated",
        "lstm_model_id": lstm_model.id,
        "lstm_version": lstm_model.version,
        "message": "LSTM model activated as baseline source",
        "activated_at": ML_RUNTIME_STATE["lstm_activated_at"],
    }


@router.post("/deactivate")
def deactivate_lstm(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    Деактивирует LSTM модель.
    Возвращает CatBoost как источник baseline.
    """
    from app.core.settings import settings
    from app.services.activity_service import ActivityService

    # Если LSTM выключена — возвращаем сообщение
    if not settings.USE_LSTM:
        return {
            "status": "not_implemented",
            "message": "LSTM deactivation is not yet available in production. "
                       "Please set USE_LSTM=True in settings when ready.",
            "docs": "See app/core/settings.py -> USE_LSTM"
        }

    if not ML_RUNTIME_STATE.get("lstm_active", False):
        raise HTTPException(
            status_code=400,
            detail="LSTM is not active. Nothing to deactivate."
        )

    lstm_model_id = ML_RUNTIME_STATE.get("lstm_model_id")

    # Деактивируем LSTM
    ML_RUNTIME_STATE["lstm_active"] = False
    ML_RUNTIME_STATE["lstm_deactivated_at"] = datetime.now(timezone.utc).isoformat()

    # Логируем действие
    ActivityService.log(
        db=db,
        user_id=current_user.id,
        action="deactivate_lstm",
        resource=f"lstm_model_{lstm_model_id}" if lstm_model_id else "lstm_model",
        details="LSTM deactivated, returning to CatBoost baseline"
    )

    logger.info(f"✅ LSTM model {lstm_model_id} deactivated by user {current_user.username}")

    return {
        "status": "deactivated",
        "message": "LSTM model deactivated. CatBoost will be used for baseline.",
        "deactivated_at": ML_RUNTIME_STATE["lstm_deactivated_at"],
    }



# ================================================================
# 📈 LSTM TRAINING METRICS FOR CHART
# ================================================================

@router.get("/training/metrics")
def get_lstm_training_metrics(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    Возвращает метрики обучения LSTM модели для графиков.
    Ищет в папке models/metrics/lstm_training_metrics.json
    """
    from pathlib import Path
    import json
    from app.core.settings import settings

    metrics_dir = Path(settings.ML_METRICS_DIR)
    metrics_path = metrics_dir / "lstm_training_metrics.json"

    if not metrics_path.exists():
        return {
            "iterations": [],
            "train_loss": [],
            "val_loss": [],
            "best_epoch": None,
            "best_val_loss": None,
            "message": "No LSTM training metrics available yet. Train LSTM model first."
        }

    try:
        with open(metrics_path) as f:
            data = json.load(f)

        return {
            "iterations": data.get("iterations", []),
            "train_loss": data.get("train_loss", []),
            "val_loss": data.get("val_loss", []),
            "best_epoch": data.get("best_epoch"),
            "best_val_loss": data.get("best_val_loss"),
            "total_epochs": len(data.get("train_loss", []))
        }
    except Exception as e:
        return {
            "iterations": [],
            "train_loss": [],
            "val_loss": [],
            "best_epoch": None,
            "best_val_loss": None,
            "error": str(e)
        }

