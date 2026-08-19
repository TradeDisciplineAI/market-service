"""create paper trade executions

Revision ID: 04d4d4d4d4d4
Revises: 03c3c3c3c3c3
Create Date: 2026-08-18 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "04d4d4d4d4d4"
down_revision: Union[str, Sequence[str], None] = "03c3c3c3c3c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "paper_trade_executions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.String(length=20), nullable=False),
        sa.Column("proposal_id", sa.UUID(), nullable=False),
        sa.Column("portfolio_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("action", sa.String(length=10), nullable=False),
        sa.Column("requested_quantity", sa.Integer(), nullable=False),
        sa.Column("filled_quantity", sa.Integer(), nullable=False),
        sa.Column("execution_price", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("stop_loss", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("take_profit", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("primary_strategy", sa.String(length=100), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("requested_quantity > 0", name="chk_paper_trade_execution_requested_quantity_positive"),
        sa.CheckConstraint("filled_quantity > 0", name="chk_paper_trade_execution_filled_quantity_positive"),
        sa.CheckConstraint("execution_price > 0", name="chk_paper_trade_execution_price_positive"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["market.portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("execution_id", name="uq_paper_trade_execution_id"),
        sa.UniqueConstraint("proposal_id", name="uq_paper_trade_execution_proposal_id"),
        schema="market"
    )
    op.create_index(
        op.f("ix_market_paper_trade_executions_execution_id"),
        "paper_trade_executions",
        ["execution_id"],
        unique=True,
        schema="market"
    )
    op.create_index(
        op.f("ix_market_paper_trade_executions_proposal_id"),
        "paper_trade_executions",
        ["proposal_id"],
        unique=True,
        schema="market"
    )
    op.create_index(
        op.f("ix_market_paper_trade_executions_portfolio_id"),
        "paper_trade_executions",
        ["portfolio_id"],
        unique=False,
        schema="market"
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_market_paper_trade_executions_portfolio_id"), table_name="paper_trade_executions", schema="market")
    op.drop_index(op.f("ix_market_paper_trade_executions_proposal_id"), table_name="paper_trade_executions", schema="market")
    op.drop_index(op.f("ix_market_paper_trade_executions_execution_id"), table_name="paper_trade_executions", schema="market")
    op.drop_table("paper_trade_executions", schema="market")
