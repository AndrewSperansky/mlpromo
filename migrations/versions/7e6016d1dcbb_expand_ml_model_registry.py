"""expand ml_model registry

Revision ID: 7e6016d1dcbb
Revises: b6f9db46bc0a
Create Date: 2026-01-12 18:08:26.549400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e6016d1dcbb'
down_revision: Union[str, Sequence[str], None] = 'b6f9db46bc0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("ml_model", sa.Column("model_type", sa.String(), nullable=False, server_default="regression"))
    op.add_column("ml_model", sa.Column("target", sa.String(), nullable=False, server_default="sales_qty"))

    op.add_column("ml_model", sa.Column("features", sa.JSON(), nullable=True))
    op.add_column("ml_model", sa.Column("metrics", sa.JSON(), nullable=True))

    op.add_column("ml_model", sa.Column("model_path", sa.Text(), nullable=True))
    op.add_column("ml_model", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))



def downgrade() -> None:
    """Downgrade schema."""
    pass
