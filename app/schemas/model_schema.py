# app/schemas/model_schema.py


from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class ModelResponse(BaseModel):
    id: int
    name: str
    version: str
    dataset_version_id: UUID
    is_active: bool
    metrics: dict | None
    trained_rows_count: int
    trained_at: datetime

    class Config:
        from_attributes = True