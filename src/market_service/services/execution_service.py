import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from market_service.core.exceptions import (
    ConflictException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
    UnprocessableEntityException,
)
from market_service.models.paper_trade_execution import PaperTradeExecution
from market_service.repositories.portfolio_repository import PortfolioRepository
from market_service.schemas.execution import (
    PaperExecutionRequest,
    PaperExecutionResponse,
)
from market_service.services.yfinance_service import YFinanceService

logger = logging.getLogger(__name__)


class ExecutionService:
    def __init__(self) -> None:
        self.portfolio_repository = PortfolioRepository()
        self.yfinance_service = YFinanceService()

    async def execute_paper_trade(
        self,
        db: AsyncSession,
        payload: PaperExecutionRequest,
    ) -> PaperExecutionResponse:
        """
        Agent 5: Execution Service (market-service side).
        Ensures idempotency, transactional safety, and portfolio validations.
        """
        # 1. Idempotency Check — return existing execution if present
        stmt = select(PaperTradeExecution).where(
            PaperTradeExecution.proposal_id == payload.proposal_id
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            logger.info(
                "Found existing execution for proposal_id %s. Returning cached result.",
                payload.proposal_id,
            )
            return PaperExecutionResponse(
                execution_id=existing.execution_id,
                proposal_id=existing.proposal_id,
                symbol=existing.symbol,
                action=existing.action,
                filled_quantity=existing.filled_quantity,
                execution_price=float(existing.execution_price),
                executed_at=existing.executed_at or datetime.now(UTC),
            )

        # 2. Basic Input Validations
        action = payload.action.strip().upper()
        if action not in ("BUY", "SELL"):
            raise UnprocessableEntityException(
                f"Unsupported execution action: {action}"
            )
        if payload.requested_quantity <= 0:
            raise UnprocessableEntityException(
                "requested_quantity must be greater than zero"
            )

        # 3. Execution Price Resolution (via YFinanceService)
        quote = await self.yfinance_service.get_stock_quote(payload.symbol)
        if not quote or quote.current_price is None or quote.current_price <= 0:
            raise UnprocessableEntityException(
                f"Could not retrieve a valid live market price for '{payload.symbol}'"
            )

        execution_price = float(quote.current_price)

        # 4. Atomic Database Mutation
        try:
            async with db.begin_nested():
                # Verify portfolio exists
                portfolio = await self.portfolio_repository.get_portfolio_by_id(
                    db, payload.portfolio_id
                )
                if not portfolio:
                    raise NotFoundException("Portfolio not found")

                # Verify ownership
                if portfolio.user_id != payload.user_id:
                    raise ForbiddenException("Portfolio does not belong to the user")

                # Apply portfolio/position updates
                await self.portfolio_repository.merge_paper_position(
                    db=db,
                    portfolio_id=payload.portfolio_id,
                    symbol=payload.symbol,
                    action=action,
                    quantity=payload.requested_quantity,
                    price=execution_price,
                )

                # Persist the execution details
                execution = PaperTradeExecution(
                    execution_id=payload.execution_id,
                    proposal_id=payload.proposal_id,
                    portfolio_id=payload.portfolio_id,
                    user_id=payload.user_id,
                    symbol=payload.symbol,
                    action=action,
                    requested_quantity=payload.requested_quantity,
                    filled_quantity=payload.requested_quantity,
                    execution_price=execution_price,
                    stop_loss=payload.stop_loss,
                    take_profit=payload.take_profit,
                    primary_strategy=payload.primary_strategy,
                )
                db.add(execution)
                await db.flush()

                # Extract all details before commit to prevent
                # MissingGreenlet due to expired attributes
                exec_id = execution.execution_id
                prop_id = execution.proposal_id
                symbol = execution.symbol
                act = execution.action
                qty = execution.filled_quantity
                price = float(execution.execution_price)
                executed_at = execution.executed_at or datetime.now(UTC)

            # Commit outer transaction
            await db.commit()

            return PaperExecutionResponse(
                execution_id=exec_id,
                proposal_id=prop_id,
                symbol=symbol,
                action=act,
                filled_quantity=qty,
                execution_price=price,
                executed_at=executed_at,
            )

        except Exception as e:
            logger.exception(
                "Paper execution transaction failed for proposal %s",
                payload.proposal_id,
            )
            if isinstance(
                e, (NotFoundException, ForbiddenException, UnprocessableEntityException)
            ):
                raise e
            from sqlalchemy.exc import IntegrityError

            if isinstance(e, IntegrityError) or "uq_paper_trade_execution" in str(e):
                raise ConflictException(
                    "Duplicate execution: proposal or execution ID already executed"
                ) from None
            raise InternalServerException(f"Paper execution failed: {e}") from e
