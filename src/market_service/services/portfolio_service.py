import asyncio
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from market_service.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    PaymentRequiredException,
)
from market_service.models.portfolio import Portfolio
from market_service.models.portfolio_holding import PortfolioHolding
from market_service.repositories.portfolio_repository import PortfolioRepository
from market_service.schemas.portfolio import (
    PaperPositionCreate,
    PaperPositionResponse,
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
    ) -> PortfolioResponse:
        existing = await self.repository.get_portfolio_by_user(db, user_id)
        if existing:
            raise ConflictException("User already has a portfolio")

        portfolio = Portfolio(
            user_id=user_id,
            name=portfolio_in.name,
            type=portfolio_in.type or "PAPER",
        )
        created = await self.repository.create_portfolio(db, portfolio)

        positions_models = [
            PaperPositionResponse(
                id=p.id,
                portfolio_id=p.portfolio_id,
                symbol=p.symbol,
                quantity=p.quantity,
                average_entry_price=float(p.average_entry_price),
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in getattr(created, "paper_positions", []) or []
        ]

        return PortfolioResponse(
            id=created.id,
            user_id=created.user_id,
            name=created.name,
            type=getattr(created, "type", "PAPER"),
            holdings=[],
            positions=positions_models,
            created_at=created.created_at,
            updated_at=created.updated_at,
        )

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

        positions_models = [
            PaperPositionResponse(
                id=p.id,
                portfolio_id=p.portfolio_id,
                symbol=p.symbol,
                quantity=p.quantity,
                average_entry_price=float(p.average_entry_price),
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in getattr(portfolio, "paper_positions", []) or []
        ]

        return PortfolioResponse(
            id=portfolio.id,
            user_id=portfolio.user_id,
            name=portfolio.name,
            type=getattr(portfolio, "type", "PAPER"),
            holdings=enriched_holdings,
            positions=positions_models,
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at,
        )

    async def get_positions(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        portfolio_id: uuid.UUID,
    ) -> list[PaperPositionResponse]:
        portfolio = await self.repository.get_portfolio_by_id(db, portfolio_id)
        if not portfolio:
            raise NotFoundException("Portfolio not found")

        if portfolio.user_id != user_id:
            raise ForbiddenException("You do not own this portfolio")

        positions = await self.repository.get_positions_by_portfolio(db, portfolio_id)
        return [
            PaperPositionResponse(
                id=p.id,
                portfolio_id=p.portfolio_id,
                symbol=p.symbol,
                quantity=p.quantity,
                average_entry_price=float(p.average_entry_price),
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in positions
        ]

    async def add_or_update_position(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        portfolio_id: uuid.UUID,
        position_in: PaperPositionCreate,
    ) -> PaperPositionResponse:
        portfolio = await self.repository.get_portfolio_by_id(db, portfolio_id)
        if not portfolio:
            raise NotFoundException("Portfolio not found")

        if portfolio.user_id != user_id:
            raise ForbiddenException("You do not own this portfolio")

        if position_in.quantity <= 0:
            raise BadRequestException("quantity must be greater than zero")

        if position_in.average_entry_price <= 0:
            raise BadRequestException("average_entry_price must be greater than zero")

        pos = await self.repository.add_or_update_paper_position(
            db,
            portfolio_id,
            position_in.symbol.strip().upper(),
            position_in.quantity,
            position_in.average_entry_price,
        )

        return PaperPositionResponse(
            id=pos.id,
            portfolio_id=pos.portfolio_id,
            symbol=pos.symbol,
            quantity=pos.quantity,
            average_entry_price=float(pos.average_entry_price),
            created_at=pos.created_at,
            updated_at=pos.updated_at,
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

        from sqlalchemy import text

        user_res = await db.execute(
            text(
                "SELECT trades_count, subscription_tier "
                "FROM authentication.users WHERE id = :user_id"
            ),
            {"user_id": user_id},
        )
        user_row = user_res.fetchone()
        if user_row:
            trades_count, tier = user_row[0], user_row[1]
            if tier != "PRO" and trades_count >= 6:
                raise PaymentRequiredException(
                    "Free trade limit reached (6/6). Upgrade to Pro."
                )

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

        await db.execute(
            text(
                "UPDATE authentication.users "
                "SET trades_count = trades_count + 1 WHERE id = :user_id"
            ),
            {"user_id": user_id},
        )
        await db.commit()

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
