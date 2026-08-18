"""add paper portfolio positions

Revision ID: 03c3c3c3c3c3
Revises: 02b2b2b2b2b2
Create Date: 2026-08-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "03c3c3c3c3c3"
down_revision: Union[str, Sequence[str], None] = "02b2b2b2b2b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "portfolios",
        sa.Column("type", sa.String(length=20), nullable=False, server_default="PAPER"),
        schema="market"
    )
    op.create_table(
        "paper_positions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("portfolio_id", sa.UUID(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("average_entry_price", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("quantity > 0", name="chk_paper_position_quantity_positive"),
        sa.CheckConstraint("average_entry_price > 0", name="chk_paper_position_price_positive"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["market.portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("portfolio_id", "symbol", name="uq_paper_position_portfolio_symbol"),
        schema="market"
    )
    op.create_index(
        op.f("ix_market_paper_positions_portfolio_id"),
        "paper_positions",
        ["portfolio_id"],
        unique=False,
        schema="market"
    )
    op.create_index(
        op.f("ix_market_paper_positions_symbol"),
        "paper_positions",
        ["symbol"],
        unique=False,
        schema="market"
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_market_paper_positions_symbol"), table_name="paper_positions", schema="market")
    op.drop_index(op.f("ix_market_paper_positions_portfolio_id"), table_name="paper_positions", schema="market")
    op.drop_table("paper_positions", schema="market")
    op.drop_column("portfolios", "type", schema="market")
