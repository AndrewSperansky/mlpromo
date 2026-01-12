"""add trained_at and is_active to ml_model

Revision ID: b6f9db46bc0a
Revises: afe095f9d6db
Create Date: 2026-01-12 17:16:34.763135

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6f9db46bc0a'
down_revision: Union[str, Sequence[str], None] = 'afe095f9d6db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ml_model",
        sa.Column(
            "trained_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.add_column(
        "ml_model",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("ml_model", "is_active")
    op.drop_column("ml_model", "trained_at")
