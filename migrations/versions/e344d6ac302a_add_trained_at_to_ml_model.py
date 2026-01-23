"""add trained_at to ml_model

Revision ID: e344d6ac302a
Revises: b06bf7e07b1b
Create Date: 2026-01-12 16:51:26.682636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e344d6ac302a'
down_revision: Union[str, Sequence[str], None] = 'b06bf7e07b1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
