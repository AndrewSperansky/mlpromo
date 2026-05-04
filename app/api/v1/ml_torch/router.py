# app/api/v1/ml_torch/router.py

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pathlib import Path

from sqlalchemy.orm import Session
from app.db.session import get_db
from app.ml_torch.train.train_pipeline import train_lstm_pipeline
from app.services.price_history_service import PriceHistoryService
from app.services.average_cheque_service import AverageChequeService
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