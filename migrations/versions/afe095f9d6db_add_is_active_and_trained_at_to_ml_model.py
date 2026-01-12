"""add is_active and trained_at to ml_model

Revision ID: afe095f9d6db
Revises: e344d6ac302a
Create Date: 2026-01-12 17:11:08.779733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'afe095f9d6db'
down_revision: Union[str, Sequence[str], None] = 'e344d6ac302a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
