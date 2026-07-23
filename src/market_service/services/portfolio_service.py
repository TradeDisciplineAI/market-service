import asyncio
import logging
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
from market_service.schemas.portfolio import (
    PortfolioCreate,
    PortfolioHoldingCreate,
    PortfolioHoldingResponse,
    PortfolioResponse,
)

logger = logging.getLogger(__name__)


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
    ) -> PortfolioResponse:
        portfolio = await self.repository.get_portfolio_by_user(db, user_id)
        if not portfolio:
            raise NotFoundException("Portfolio not found")

        from market_service.services.yfinance_service import YFinanceService

        yfinance_service = YFinanceService()

        enriched_holdings = []
        if portfolio.holdings:
            try:
                quotes = await asyncio.wait_for(
                    asyncio.gather(
                        *(
                            yfinance_service.get_stock_quote(h.symbol)
                            for h in portfolio.holdings
                        )
                    ),
                    timeout=2.5,
                )
            except TimeoutError:
                logger.warning(
                    "YFinance quote fetch timed out, returning cached/None values"
                )
                quotes = [None] * len(portfolio.holdings)

            for h, q in zip(portfolio.holdings, quotes, strict=True):
                holding_model = PortfolioHoldingResponse(
                    id=h.id,
                    portfolio_id=h.portfolio_id,
                    symbol=h.symbol,
                    created_at=h.created_at,
                    price=q.current_price if q else None,
                    percent_change=q.percent_change if q else None,
                    currency=q.currency if q else "USD",
                )
                enriched_holdings.append(holding_model)

        return PortfolioResponse(
            id=portfolio.id,
            user_id=portfolio.user_id,
            name=portfolio.name,
            holdings=enriched_holdings,
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at,
        )

    async def add_holding(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        holding_in: PortfolioHoldingCreate,
    ) -> PortfolioHoldingResponse:
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

        from market_service.services.yfinance_service import YFinanceService

        yfinance_service = YFinanceService()
        q = await yfinance_service.get_stock_quote(symbol)

        if not q or q.current_price is None:
            raise BadRequestException(f"Invalid or unsupported stock symbol '{symbol}'")

        holding = PortfolioHolding(
            portfolio_id=portfolio.id,
            symbol=symbol,
        )
        saved_holding = await self.repository.add_holding(db, holding)

        return PortfolioHoldingResponse(
            id=saved_holding.id,
            portfolio_id=saved_holding.portfolio_id,
            symbol=saved_holding.symbol,
            created_at=saved_holding.created_at,
            price=q.current_price,
            percent_change=q.percent_change,
            currency=q.currency or "USD",
        )

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
