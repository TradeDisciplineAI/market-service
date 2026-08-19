from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from market_service.core.database import Base

if TYPE_CHECKING:
    from .paper_position import PaperPosition
    from .portfolio_holding import PortfolioHolding
    from .paper_trade_execution import PaperTradeExecution


class Portfolio(Base):
    __tablename__ = "portfolios"
    __table_args__ = {"schema": "market"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PAPER",
        server_default="PAPER",
    )

    holdings: Mapped[list[PortfolioHolding]] = relationship(
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )

    paper_positions: Mapped[list[PaperPosition]] = relationship(
        "PaperPosition",
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )

    paper_trade_executions: Mapped[list[PaperTradeExecution]] = relationship(
        "PaperTradeExecution",
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
