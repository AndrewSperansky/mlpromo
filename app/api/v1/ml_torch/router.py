# app/api/v1/ml_torch/router.py

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pathlib import Path
from pydantic import BaseModel, Field
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
    TrainLSTMResponse,
    PredictLSTMRequest,
    PredictLSTMResponse,
    PriceHistoryResponse,
    PriceHistoryItem,
    AverageChequePushRequest,
    SalesFactPushRequest,
    ExchangeRatePushRequest,
    CalendarPushRequest,
)

router = APIRouter(tags=["ml_torch"])

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
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Обучает LSTM модель для прогнозирования цен на основе истории.

    Требует наличия данных в таблице retail_price_history.
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
            promote=request.promote
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ПРОГНОЗ
# ============================================================

@router.post("/predict/lstm", response_model=PredictLSTMResponse)
def predict_lstm(
        request: PredictLSTMRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Прогнозирует цены с использованием активной LSTM модели.

    Для работы требуется:
    1. Активная LSTM модель в реестре (algorithm='pytorch_lstm')
    2. История цен SKU в таблице retail_price_history
    """
    # Находим активную LSTM модель
    registry = ModelRegistryService(db)

    # Ищем активную модель с нужным алгоритмом
    # TODO: добавить фильтр по algorithm в registry
    active_models = registry.list_models()
    lstm_model = None
    for m in active_models:
        if m.algorithm == "pytorch_lstm" and m.is_active:
            lstm_model = m
            break

    if not lstm_model:
        raise HTTPException(
            status_code=404,
            detail="Нет активной LSTM модели. Сначала обучите и активируйте модель."
        )

    # Загружаем модель
    predictor = TorchPredictor(db)

    # Загружаем конфигурацию из meta.json
    import json
    meta_path = Path(lstm_model.model_path).with_suffix('.meta.json')
    if meta_path.exists():
        with open(meta_path) as f:
            config = json.load(f)
            model_config = config.get("model_config", {})
    else:
        model_config = {
            "input_size": 1,
            "hidden_size": 64,
            "num_layers": 2,
            "seq_len": 30
        }

    predictor.load_model(Path(lstm_model.model_path), model_config)

    # Делаем прогноз
    try:
        predictions = predictor.predict_prices_forecast(
            sku=request.sku,
            forecast_days=request.days_ahead,
            seq_len=model_config.get("seq_len", 30)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
        current_user: User = Depends(get_current_user)
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
    result = await service.process_push_data(db, records, request.batch_id)

    return result

# ================================================
# POST запрос от 1С ПРОДАЖИ
# ================================================

@router.post("/push/sales-fact")
async def push_sales_fact(
    request: SalesFactPushRequest,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)  # временно отключаем
):
    """
    PUSH-приём данных о продажах из 1С.
    """
    service = SalesFactService()
    result = await service.process_push_data(db, request.records, request.batch_id)
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

# ================================================
# Эндпоинт для обучения LSTM
# ================================================

class TrainLSTMRequest(BaseModel):
    sku: str = Field(..., description="SKU товара")
    days: int = Field(365, ge=30, le=730)
    seq_len: int = Field(30, ge=7, le=90)
    hidden_size: int = Field(64, ge=16, le=256)
    num_layers: int = Field(2, ge=1, le=4)
    learning_rate: float = Field(0.001, gt=0, le=0.1)
    batch_size: int = Field(32, ge=8, le=128)
    epochs: int = Field(50, ge=10, le=200)
    promote: bool = Field(False)


@router.post("/train/lstm")
async def train_lstm(
        request: TrainLSTMRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
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

