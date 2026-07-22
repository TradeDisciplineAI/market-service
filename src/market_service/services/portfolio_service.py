import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from market_service.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from market_service.models.portfolio import Portfolio
from market_service.models.portfolio_holding import PortfolioHolding
from market_service.repositories.portfolio_repository import PortfolioRepository
from market_service.schemas.portfolio import PortfolioCreate, PortfolioHoldingCreate


class PortfolioService:
    def __init__(self) -> None:
        self.repository = PortfolioRepository()

    async def create_portfolio(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        portfolio_in: PortfolioCreate,
    ) -> Portfolio:
        existing = await self.repository.get_portfolio_by_user(db, user_id)
        if existing:
            raise ConflictException("User already has a portfolio")

        portfolio = Portfolio(
            user_id=user_id,
            name=portfolio_in.name,
        )
        return await self.repository.create_portfolio(db, portfolio)

    async def get_portfolio(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Portfolio:
        portfolio = await self.repository.get_portfolio_by_user(db, user_id)
        if not portfolio:
            raise NotFoundException("Portfolio not found")
        return portfolio

    async def add_holding(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        holding_in: PortfolioHoldingCreate,
    ) -> PortfolioHolding:
        portfolio = await self.repository.get_portfolio_by_user(db, user_id)
        if not portfolio:
            raise NotFoundException("Portfolio not found")

        if portfolio.user_id != user_id:
            raise ForbiddenException("You do not own this portfolio")

        symbol = holding_in.symbol.strip().upper()

        for h in portfolio.holdings:
            if h.symbol == symbol:
                raise ConflictException("Stock symbol already exists in portfolio")

        if len(portfolio.holdings) >= 5:
            raise BadRequestException("Portfolio cannot contain more than 5 stocks")

        holding = PortfolioHolding(
            portfolio_id=portfolio.id,
            symbol=symbol,
        )
        return await self.repository.add_holding(db, holding)

    async def remove_holding(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        symbol: str,
    ) -> None:
        portfolio = await self.repository.get_portfolio_by_user(db, user_id)
        if not portfolio:
            raise NotFoundException("Portfolio not found")

        normalized_symbol = symbol.strip().upper()

        target_holding = None
        for h in portfolio.holdings:
            if h.symbol == normalized_symbol:
                target_holding = h
                break

        if not target_holding:
            raise NotFoundException("Stock symbol not found in portfolio")

        await self.repository.remove_holding(db, target_holding)
