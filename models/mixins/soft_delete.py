# SoftDeleteMixin (опционально, но полезно)
from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    deleted_at: Mapped = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
