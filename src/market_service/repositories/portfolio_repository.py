import uuid
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from market_service.core.exceptions import UnprocessableEntityException
from market_service.models.paper_position import PaperPosition
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
            .options(
                selectinload(Portfolio.holdings),
                selectinload(Portfolio.paper_positions),
            )
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
            .options(
                selectinload(Portfolio.holdings),
                selectinload(Portfolio.paper_positions),
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_portfolio_by_id(
        self,
        db: AsyncSession,
        portfolio_id: uuid.UUID,
    ) -> Portfolio | None:
        stmt = (
            select(Portfolio)
            .where(Portfolio.id == portfolio_id)
            .options(
                selectinload(Portfolio.holdings),
                selectinload(Portfolio.paper_positions),
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_positions_by_portfolio(
        self,
        db: AsyncSession,
        portfolio_id: uuid.UUID,
    ) -> list[PaperPosition]:
        stmt = select(PaperPosition).where(PaperPosition.portfolio_id == portfolio_id)
        result = await db.execute(stmt)
        return cast(list[PaperPosition], list(result.scalars().all()))

    async def add_or_update_paper_position(
        self,
        db: AsyncSession,
        portfolio_id: uuid.UUID,
        symbol: str,
        quantity: int,
        average_entry_price: float,
    ) -> PaperPosition:
        stmt = select(PaperPosition).where(
            PaperPosition.portfolio_id == portfolio_id,
            PaperPosition.symbol == symbol,
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            existing.quantity = quantity
            existing.average_entry_price = average_entry_price
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            pos = PaperPosition(
                portfolio_id=portfolio_id,
                symbol=symbol,
                quantity=quantity,
                average_entry_price=average_entry_price,
            )
            db.add(pos)
            await db.commit()
            await db.refresh(pos)
            return pos

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

    async def merge_paper_position(
        self,
        db: AsyncSession,
        portfolio_id: uuid.UUID,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
    ) -> PaperPosition | None:
        stmt = select(PaperPosition).where(
            PaperPosition.portfolio_id == portfolio_id,
            PaperPosition.symbol == symbol,
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()

        action_upper = action.upper()
        if action_upper == "BUY":
            if not existing:
                pos = PaperPosition(
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    quantity=quantity,
                    average_entry_price=price,
                )
                db.add(pos)
                await db.flush()
                return pos
            else:
                new_qty = existing.quantity + quantity
                # Merge average entry price:
                # (existing_qty * existing_price + new_qty * price) / new_qty
                # average_entry_price is Decimal/Numeric; cast to float then back
                new_avg = (
                    (existing.quantity * float(existing.average_entry_price))
                    + (quantity * price)
                ) / new_qty
                existing.quantity = new_qty
                existing.average_entry_price = new_avg
                await db.flush()
                return existing

        elif action_upper == "SELL":
            if not existing:
                raise UnprocessableEntityException(
                    "SELL order requires an existing paper position."
                )
            if quantity > existing.quantity:
                raise UnprocessableEntityException(
                    "Cannot SELL more than the available quantity."
                )

            if quantity == existing.quantity:
                await db.delete(existing)
                await db.flush()
                return None
            else:
                existing.quantity -= quantity
                # average_entry_price is unchanged on SELL
                await db.flush()
                return existing
        else:
            raise UnprocessableEntityException(f"Unsupported merge action: {action}")
