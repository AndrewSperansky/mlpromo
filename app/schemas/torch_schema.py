# app/schemas/torch_schema.py

"""
Pydantic схемы для PyTorch модуля (ml_torch)

Схемы — это «контракты» данных:
- описывают, что приходит в запросе (Request)
- и что возвращается в ответе (Response)
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import date as date_type


# ============================================
# ЗАПРОСЫ (REQUEST)
# ============================================

class TrainLSTMRequest(BaseModel):
    """
    Запрос на обучение LSTM модели.

    LSTM = Long Short-Term Memory (рус. «Долгая краткосрочная память»)
    """
    sku: str = Field(..., description="SKU товара")

    # Параметры данных
    days: int = Field(365, ge=30, le=730, description="Сколько дней истории брать (30-730)")
    seq_len: int = Field(30, ge=7, le=90, description="Длина окна истории (7-90 дней)")

    # Гиперпараметры модели
    hidden_size: int = Field(64, ge=16, le=256, description="Размер скрытого состояния LSTM")
    num_layers: int = Field(2, ge=1, le=4, description="Количество слоёв LSTM")

    # Параметры обучения
    learning_rate: float = Field(0.001, gt=0, le=0.1, description="Скорость обучения")
    batch_size: int = Field(32, ge=8, le=128, description="Размер батча")
    epochs: int = Field(50, ge=10, le=200, description="Количество эпох обучения")

    # Управление
    promote: bool = Field(False, description="Активировать модель сразу после обучения")


class TrainMLPRequest(BaseModel):
    """
    Запрос на обучение MLP модели (многослойный перцептрон)
    """
    sku: str = Field(..., description="SKU товара")
    days: int = Field(365, ge=30, le=730, description="Сколько дней истории брать")

    # Гиперпараметры MLP
    hidden_dims: List[int] = Field([128, 64, 32], description="Размеры скрытых слоёв")
    dropout: float = Field(0.2, ge=0.0, le=0.5, description="Доля отключаемых нейронов")

    # Параметры обучения
    learning_rate: float = Field(0.001, gt=0, le=0.1)
    batch_size: int = Field(32, ge=8, le=128)
    epochs: int = Field(50, ge=10, le=200)
    promote: bool = Field(False)


class PredictLSTMRequest(BaseModel):
    """
    Запрос на предсказание с использованием LSTM модели
    """
    sku: str = Field(..., description="SKU товара")
    days_ahead: int = Field(1, ge=1, le=30, description="На сколько дней вперёд прогноз")





# ============================================
# ОТВЕТЫ (RESPONSE)
# ============================================

class PriceHistoryItem(BaseModel):
    """Одна запись в истории цен"""
    date: str = Field(..., description="Дата (YYYY-MM-DD)")
    price: float = Field(..., description="Цена")


class PriceHistoryResponse(BaseModel):
    """Ответ с историей цен"""
    sku: str = Field(..., description="SKU товара")
    days: int = Field(..., description="Запрошенное количество дней")
    history: List[PriceHistoryItem] = Field(default_factory=list, description="Список записей")


class TrainLSTMResponse(BaseModel):
    """Ответ после обучения LSTM модели"""
    status: str = Field(..., description="Статус операции (success/error)")
    model_id: Optional[int] = Field(None, description="ID модели в реестре")
    sku: str = Field(..., description="SKU товара")
    best_val_loss: Optional[float] = Field(None, description="Лучшая ошибка на валидации")
    epochs_completed: int = Field(0, description="Количество завершённых эпох")
    promoted: bool = Field(False, description="Была ли модель активирована")
    message: Optional[str] = Field(None, description="Дополнительное сообщение")


# ============================================
# Средний чек
# ============================================

class AverageChequeRecord(BaseModel):
    date: date_type
    store_code: str
    store_name: str
    cheque_count: int
    total_amount: float
    average_amount: float
    is_total: int  # 0 или 1

class AverageChequePushRequest(BaseModel):
    """Формат данных, который 1С отправляет в Promo-ML"""
    records: List[AverageChequeRecord]


# ============================================
# Продажи
# ============================================

class SalesFactRecord(BaseModel):
    """Одна запись продаж"""
    date: date_type
    week: int
    sku_code: str
    sku_name: Optional[str] = None
    store_code: str
    store_name: Optional[str] = None
    region: Optional[str] = None
    oblast: Optional[str] = None
    uom: Optional[str] = None
    quantity: int
    revenue: float
    category: Optional[str] = None


class SalesFactPushRequest(BaseModel):
    """PUSH-запрос продаж из 1С"""
    records: List[SalesFactRecord]

# ============================================
# Курсы валют
# ============================================

class ExchangeRateRecord(BaseModel):
    date: date_type
    currency: str  # USD, EUR, CNY
    rate: float


class ExchangeRatePushRequest(BaseModel):
    records: List[ExchangeRateRecord]


# ============================================
# Календарь
# ============================================

class CalendarRecord(BaseModel):
    date: date_type
    day_type: str      # Праздник, Суббота, Воскресенье, Рабочий, Предпраздничный
    week: int          # номер недели
    year: int


class CalendarPushRequest(BaseModel):
    records: List[CalendarRecord]


# ============================================================
# PUSH запросы для загрузки цен
# ============================================================

class RetailPriceRecord(BaseModel):
    date: date_type = Field(..., description="Дата (конец недели)")
    week: int = Field(..., ge=1, le=53, description="Номер недели")
    sku_code: str = Field(..., description="SKU товара")
    sku_name: Optional[str] = Field(None, description="Наименование товара")
    category: Optional[str] = Field(None, description="Категория 2-го уровня")
    price: float = Field(..., gt=0, description="Цена")

class RetailPricePushRequest(BaseModel):
    records: List[RetailPriceRecord] = Field(..., description="Список записей цен")



class PurchasePriceRecord(BaseModel):
    date: date_type = Field(..., description="Дата")
    sku: str = Field(..., description="SKU товара")
    supplier: str = Field(..., description="Поставщик")
    price: float = Field(..., gt=0, description="Закупочная цена")

class PurchasePricePushRequest(BaseModel):
    records: List[PurchasePriceRecord] = Field(..., description="Список записей закупочных цен")




# ============================================
# LSTM Model Prediction
# ============================================


class PredictLSTMResponse(BaseModel):
    """Ответ с прогнозом LSTM модели"""
    sku: str = Field(..., description="SKU товара")
    days_ahead: int = Field(..., description="Горизонт прогноза")
    predictions: List[Dict[str, Any]] = Field(..., description="Список прогнозов по дням")
    model_id: Optional[int] = Field(None, description="ID использованной модели")


class ModelInfoResponse(BaseModel):
    """Информация о torch-модели"""
    id: int
    name: str
    version: str
    algorithm: str
    model_type: str
    is_active: bool
    metrics: Optional[Dict[str, Any]]
    created_at: str