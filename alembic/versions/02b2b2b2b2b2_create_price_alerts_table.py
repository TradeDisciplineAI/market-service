"""create price alerts table

Revision ID: 02b2b2b2b2b2
Revises: 01a1a1a1a1a1
Create Date: 2026-07-25 15:17:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02b2b2b2b2b2'
down_revision: Union[str, Sequence[str], None] = '01a1a1a1a1a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "price_alerts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("target_price", sa.Float(), nullable=False),
        sa.Column("condition", sa.String(length=10), nullable=False),
        sa.Column("is_triggered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="market",
    )

    op.create_index(
        op.f("ix_market_price_alerts_user_id"),
        "price_alerts",
        ["user_id"],
        unique=False,
        schema="market",
    )

    op.create_index(
        op.f("ix_market_price_alerts_symbol"),
        "price_alerts",
        ["symbol"],
        unique=False,
        schema="market",
    )

    op.create_index(
        op.f("ix_market_price_alerts_is_triggered"),
        "price_alerts",
        ["is_triggered"],
        unique=False,
        schema="market",
    )

    op.create_index(
        "ix_price_alerts_symbol_active",
        "price_alerts",
        ["symbol", "is_triggered"],
        unique=False,
        schema="market",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_price_alerts_symbol_active",
        table_name="price_alerts",
        schema="market",
    )
    op.drop_index(
        op.f("ix_market_price_alerts_is_triggered"),
        table_name="price_alerts",
        schema="market",
    )
    op.drop_index(
        op.f("ix_market_price_alerts_symbol"),
        table_name="price_alerts",
        schema="market",
    )
    op.drop_index(
        op.f("ix_market_price_alerts_user_id"),
        table_name="price_alerts",
        schema="market",
    )
    op.drop_table(
        "price_alerts",
        schema="market",
    )
