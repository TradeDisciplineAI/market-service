from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from market_service.core.database import Base

if TYPE_CHECKING:
    from .portfolio import Portfolio


class PaperTradeExecution(Base):
    __tablename__ = "paper_trade_executions"
    __table_args__ = (
        UniqueConstraint("execution_id", name="uq_paper_trade_execution_id"),
        UniqueConstraint("proposal_id", name="uq_paper_trade_execution_proposal_id"),
        CheckConstraint(
            "requested_quantity > 0",
            name="chk_paper_trade_execution_requested_quantity_positive",
        ),
        CheckConstraint(
            "filled_quantity > 0",
            name="chk_paper_trade_execution_filled_quantity_positive",
        ),
        CheckConstraint(
            "execution_price > 0", name="chk_paper_trade_execution_price_positive"
        ),
        {"schema": "market"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    execution_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market.portfolios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    requested_quantity: Mapped[int] = mapped_column(
        nullable=False,
    )

    filled_quantity: Mapped[int] = mapped_column(
        nullable=False,
    )

    execution_price: Mapped[float] = mapped_column(
        Numeric(18, 4),
        nullable=False,
    )

    stop_loss: Mapped[float] = mapped_column(
        Numeric(18, 4),
        nullable=False,
    )

    take_profit: Mapped[float] = mapped_column(
        Numeric(18, 4),
        nullable=False,
    )

    primary_strategy: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    portfolio: Mapped[Portfolio] = relationship(
        back_populates="paper_trade_executions",
    )
