# app/schemas/dataset_schema_csv.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class TrainRequest(BaseModel):
    """Запрос на обучение модели"""
    promote: bool = Field(False, description="Автоматически продвигать модель после обучения")


class TrainResponse(BaseModel):
    """Ответ от обучения модели"""
    status: str
    model_id: int
    model_name: str
    total_rows: int
    rows_removed: int = 0
    metrics: Dict[str, Any]
    promoted: bool = False
    stage: Optional[str] = None
    note: Optional[str] = None


class DatasetInfo(BaseModel):
    """Информация о текущем датасете"""
    total_rows: int
    last_upload_at: Optional[str] = None
    last_upload_records: int = 0
    total_uploads: int = 0
    recent_uploads: list = []