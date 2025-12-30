"""rename promo_code to code

Revision ID: 8c88efdaa29a
Revises: 13460cc58f93
Create Date: 2025-12-30 11:10:40.796743

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c88efdaa29a'
down_revision: Union[str, Sequence[str], None] = '13460cc58f93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "promo",
        "promo_code",
        new_column_name="code",
        existing_type=sa.String(length=50),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "promo",
        "code",
        new_column_name="promo_code",
        existing_type=sa.String(length=50),
        existing_nullable=False,
    )
