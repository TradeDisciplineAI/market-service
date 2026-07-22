"""increase symbol length

Revision ID: 01a1a1a1a1a1
Revises: 00f2a705ae57
Create Date: 2026-07-22 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01a1a1a1a1a1'
down_revision: Union[str, Sequence[str], None] = '00f2a705ae57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'portfolio_holdings',
        'symbol',
        type_=sa.String(length=20),
        existing_type=sa.String(length=10),
        schema='market'
    )


def downgrade() -> None:
    op.alter_column(
        'portfolio_holdings',
        'symbol',
        type_=sa.String(length=10),
        existing_type=sa.String(length=20),
        schema='market'
    )
