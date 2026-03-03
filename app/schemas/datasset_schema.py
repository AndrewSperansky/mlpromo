# app/schemas/datasset_schema.py

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DatasetVersionResponse(BaseModel):
    id: UUID
    created_at: datetime
    rows_count: int

    class Config:
        from_attributes = True