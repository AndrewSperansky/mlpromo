# app/schemas/dataset_schema.py

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any


class DatasetVersionResponse(BaseModel):
    dataset_version_id: UUID = Field(..., alias="id")  # alias позволяет использовать id в БД
    created_at: datetime
    row_count: int
    target_column: str
    status: str
    comment: str | None

    class Config:
        from_attributes = True
        populate_by_name = True  # позволяет обращаться и по id, и по dataset_version_id


# Добавляем новый response для обучения на всех датасетах
class TrainOnAllResponse(BaseModel):
    status: str
    model_id: int
    model_name: str
    datasets_used: List[str]
    total_rows: int
    metrics: Dict[str, Any]
    promoted: bool = False
    stage: Optional[str] = None
    note: Optional[str] = None


# Обновляем request для train
class TrainRequest(BaseModel):
    dataset_version_id: Optional[UUID] = None  # теперь может быть None
    train_on_all: bool = False
    promote: bool = False


class TrainSingleResponse(BaseModel):
    """Ответ от обучения на одном датасете"""
    status: str
    model_id: int
    metrics: Dict[str, Any]
    promoted: bool = False
    stage: Optional[str] = None
    promotion_decision: Optional[Dict] = None
    rows_original: Optional[int] = None
    rows_used: Optional[int] = None
    rows_removed: Optional[int] = None
    model_name: str = "promo_uplift"