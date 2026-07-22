import uuid
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from market_service.models.portfolio import Portfolio
from market_service.models.portfolio_holding import PortfolioHolding


class PortfolioRepository:
    async def create_portfolio(
        self,
        db: AsyncSession,
        portfolio: Portfolio,
    ) -> Portfolio:
        db.add(portfolio)
        await db.commit()
        stmt = (
            select(Portfolio)
            .where(Portfolio.id == portfolio.id)
            .options(selectinload(Portfolio.holdings))
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    async def get_portfolio_by_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Portfolio | None:
        stmt = (
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .options(selectinload(Portfolio.holdings))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_holding(
        self,
        db: AsyncSession,
        holding: PortfolioHolding,
    ) -> PortfolioHolding:
        db.add(holding)
        await db.commit()
        await db.refresh(holding)
        return holding

    async def remove_holding(
        self,
        db: AsyncSession,
        holding: PortfolioHolding,
    ) -> None:
        await db.delete(holding)
        await db.commit()

    async def list_holdings(
        self,
        db: AsyncSession,
        portfolio_id: uuid.UUID,
    ) -> list[PortfolioHolding]:
        stmt = select(PortfolioHolding).where(
            PortfolioHolding.portfolio_id == portfolio_id
        )
        result = await db.execute(stmt)
        return cast(list[PortfolioHolding], list(result.scalars().all()))
