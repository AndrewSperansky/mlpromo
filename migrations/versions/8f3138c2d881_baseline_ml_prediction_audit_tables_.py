"""baseline: ml prediction audit tables present

Revision ID: 8f3138c2d881
Revises: 7e6016d1dcbb
Create Date: 2026-01-30 15:41:32.505340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f3138c2d881'
down_revision: Union[str, Sequence[str], None] = '7e6016d1dcbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
