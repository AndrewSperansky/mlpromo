# app/schemas/audit_schema.py


from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class AuditRecord(BaseModel):

    id: int
    request_id: UUID
    model_id: int
    model_version: str | None
    prediction_value: float | None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditPage(BaseModel):

    items: list[AuditRecord]

    page: int
    total: int