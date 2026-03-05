# app/schemas/dataset_schema.py


from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


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