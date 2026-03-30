# app/schemas/dataset_schema_csv.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class TrainRequest(BaseModel):
    """Запрос на обучение модели (всегда на всех данных)"""
    promote: bool = Field(False, description="Автоматически продвигать модель после обучения")


class TrainResponse(BaseModel):
    """Ответ от обучения модели"""
    status: str
    model_id: int
    model_name: str
    total_rows: int
    metrics: Dict[str, Any]
    promoted: bool = False
    stage: Optional[str] = None
    note: Optional[str] = None


class DatasetInfo(BaseModel):
    """Информация о текущем датасете"""
    total_rows: int
    created_at: datetime
    updated_at: datetime
    columns: List[str]