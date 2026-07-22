"""create portfolio tables

Revision ID: 00f2a705ae57
Revises:
Create Date: 2026-07-22 10:14:36.711488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '00f2a705ae57'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS market")
    op.create_table(
        "portfolios",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="market",
    )

    op.create_index(
        op.f("ix_market_portfolios_user_id"),
        "portfolios",
        ["user_id"],
        unique=False,
        schema="market",
    )

    op.create_table(
        "portfolio_holdings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("portfolio_id", sa.UUID(), nullable=False),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["portfolio_id"],
            ["market.portfolios.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "portfolio_id",
            "symbol",
            name="uq_portfolio_symbol",
        ),
        schema="market",
    )

    op.create_index(
        op.f("ix_market_portfolio_holdings_portfolio_id"),
        "portfolio_holdings",
        ["portfolio_id"],
        unique=False,
        schema="market",
    )

    op.create_index(
        op.f("ix_market_portfolio_holdings_symbol"),
        "portfolio_holdings",
        ["symbol"],
        unique=False,
        schema="market",
    )

def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_market_portfolio_holdings_symbol"),
        table_name="portfolio_holdings",
        schema="market",
    )

    op.drop_index(
        op.f("ix_market_portfolio_holdings_portfolio_id"),
        table_name="portfolio_holdings",
        schema="market",
    )

    op.drop_table(
        "portfolio_holdings",
        schema="market",
    )

    op.drop_index(
        op.f("ix_market_portfolios_user_id"),
        table_name="portfolios",
        schema="market",
    )

    op.drop_table(
        "portfolios",
        schema="market",
    )
    op.execute("DROP SCHEMA IF EXISTS market CASCADE")
