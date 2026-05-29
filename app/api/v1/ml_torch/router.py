# app/api/v1/ml_torch/router.py

import json
import logging
from datetime import date, timedelta
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

