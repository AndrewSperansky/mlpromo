"""add unique constraint to promo_position

Revision ID: b06bf7e07b1b
Revises: 8c88efdaa29a
Create Date: 2025-12-30 15:47:02.937942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b06bf7e07b1b'
down_revision: Union[str, Sequence[str], None] = '8c88efdaa29a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_promo_position_promo_product_date",
        "promo_position",
        ["promo_id", "product_id", "date"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_promo_position_promo_product_date",
        "promo_position",
        type_="unique",
    )
