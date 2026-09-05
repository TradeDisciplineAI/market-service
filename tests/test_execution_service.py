import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from market_service.core.config import get_settings
from market_service.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    UnprocessableEntityException,
)
from market_service.models.paper_position import PaperPosition
from market_service.models.paper_trade_execution import PaperTradeExecution
from market_service.models.portfolio import Portfolio
from market_service.schemas.execution import PaperExecutionRequest
from market_service.schemas.stock import StockQuote
from market_service.services.execution_service import ExecutionService


@pytest.fixture
def execution_service() -> ExecutionService:
    return ExecutionService()


@pytest.fixture
def sample_payload() -> PaperExecutionRequest:
    return PaperExecutionRequest(
        proposal_id=uuid.uuid4(),
        execution_id="EXE-TEST1234",
        portfolio_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        symbol="AAPL",
        action="BUY",
        requested_quantity=10,
        stop_loss=170.0,
        take_profit=190.0,
        primary_strategy="EMACrossover",
    )


# ─────────────────────────────────────────────────────────────────────────────
# UNIT TESTS (With Mocked Database)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("market_service.services.yfinance_service.YFinanceService.get_stock_quote")
@patch(
    "market_service.repositories.portfolio_repository.PortfolioRepository.get_portfolio_by_id"
)
@patch(
    "market_service.repositories.portfolio_repository.PortfolioRepository.merge_paper_position"
)
async def test_successful_buy_new_position(
    mock_merge,
    mock_get_portfolio,
    mock_quote,
    execution_service,
    sample_payload,
) -> None:
    """1. BUY creates new position successfully (unit test)"""
    db = AsyncMock(spec=AsyncSession)

    portfolio = Portfolio(
        id=sample_payload.portfolio_id,
        user_id=sample_payload.user_id,
        name="Test Portfolio",
        type="PAPER",
    )
    mock_get_portfolio.return_value = portfolio

    mock_quote.return_value = StockQuote(
        symbol="AAPL",
        current_price=175.50,
        change=1.2,
        percent_change=0.7,
        high=176.0,
        low=174.0,
        open_price=174.5,
        previous_close=174.3,
        currency="USD",
    )

    # Use MagicMock for DB Result (non-awaited calls)
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    res = await execution_service.execute_paper_trade(db, sample_payload)

    # Asserts
    assert res.execution_id == "EXE-TEST1234"
    assert res.proposal_id == sample_payload.proposal_id
    assert res.symbol == "AAPL"
    assert res.action == "BUY"
    assert res.filled_quantity == 10
    assert res.execution_price == 175.50

    mock_merge.assert_called_once_with(
        db=db,
        portfolio_id=sample_payload.portfolio_id,
        symbol="AAPL",
        action="BUY",
        quantity=10,
        price=175.50,
    )


@pytest.mark.asyncio
@patch("market_service.services.yfinance_service.YFinanceService.get_stock_quote")
@patch(
    "market_service.repositories.portfolio_repository.PortfolioRepository.get_portfolio_by_id"
)
async def test_portfolio_not_found(
    mock_get_portfolio,
    mock_quote,
    execution_service,
    sample_payload,
) -> None:
    """10. Portfolio not found (unit test)"""
    db = AsyncMock(spec=AsyncSession)
    mock_get_portfolio.return_value = None  # Portfolio doesn't exist
    mock_quote.return_value = StockQuote(
        symbol="AAPL", current_price=175.50, change=0, percent_change=0
    )

    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    with pytest.raises(NotFoundException) as exc:
        await execution_service.execute_paper_trade(db, sample_payload)
    assert exc.value.detail == "Portfolio not found"


@pytest.mark.asyncio
@patch("market_service.services.yfinance_service.YFinanceService.get_stock_quote")
@patch(
    "market_service.repositories.portfolio_repository.PortfolioRepository.get_portfolio_by_id"
)
async def test_portfolio_ownership_failure(
    mock_get_portfolio,
    mock_quote,
    execution_service,
    sample_payload,
) -> None:
    """11. Portfolio ownership failure (unit test)"""
    db = AsyncMock(spec=AsyncSession)

    portfolio = Portfolio(
        id=sample_payload.portfolio_id,
        user_id=uuid.uuid4(),  # Different owner
        name="Test Portfolio",
        type="PAPER",
    )
    mock_get_portfolio.return_value = portfolio
    mock_quote.return_value = StockQuote(
        symbol="AAPL", current_price=175.50, change=0, percent_change=0
    )

    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    with pytest.raises(ForbiddenException) as exc:
        await execution_service.execute_paper_trade(db, sample_payload)
    assert "belong" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_invalid_action(execution_service, sample_payload) -> None:
    """12. Invalid action (unit test)"""
    db = AsyncMock(spec=AsyncSession)
    sample_payload.action = "HOLD"

    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    with pytest.raises(UnprocessableEntityException) as exc:
        await execution_service.execute_paper_trade(db, sample_payload)
    assert "Unsupported execution action" in exc.value.detail


@pytest.mark.asyncio
async def test_invalid_quantity(execution_service, sample_payload) -> None:
    """13. Invalid quantity (unit test)"""
    db = AsyncMock(spec=AsyncSession)
    sample_payload.requested_quantity = -5

    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    with pytest.raises(UnprocessableEntityException) as exc:
        await execution_service.execute_paper_trade(db, sample_payload)
    assert "greater than zero" in exc.value.detail


@pytest.mark.asyncio
async def test_execution_idempotency_proposal_id(
    execution_service, sample_payload
) -> None:
    """8. Execution idempotency by proposal_id (unit test)"""
    db = AsyncMock(spec=AsyncSession)

    existing_execution = PaperTradeExecution(
        execution_id="EXE-CACHED123",
        proposal_id=sample_payload.proposal_id,
        portfolio_id=sample_payload.portfolio_id,
        user_id=sample_payload.user_id,
        symbol="AAPL",
        action="BUY",
        requested_quantity=10,
        filled_quantity=10,
        execution_price=170.00,
        stop_loss=160.0,
        take_profit=185.0,
        primary_strategy="EMACrossover",
        executed_at=datetime.now(UTC),
    )

    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = existing_execution
    db.execute.return_value = db_result

    res = await execution_service.execute_paper_trade(db, sample_payload)

    # Should return existing execution details without hitting yfinance
    assert res.execution_id == "EXE-CACHED123"
    assert res.execution_price == 170.00


# ─────────────────────────────────────────────────────────────────────────────
# DB INTEGRATION TESTS (With Real Postgres db_session)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("market_service.services.yfinance_service.YFinanceService.get_stock_quote")
async def test_db_buy_merges_existing_position(
    mock_quote, db_session, execution_service
) -> None:
    """2 & 3. BUY merges existing position and calculates correct weighted-average entry price"""
    mock_quote.return_value = StockQuote(
        symbol="AAPL", current_price=100.00, change=0, percent_change=0
    )

    user_id = uuid.uuid4()
    portfolio_id = uuid.uuid4()
    # 1. Create Portfolio in DB
    portfolio = Portfolio(id=portfolio_id, user_id=user_id, name="Active Portfolio")
    db_session.add(portfolio)

    # 2. Create Existing Position (10 shares at $80.0)
    position = PaperPosition(
        portfolio_id=portfolio_id, symbol="AAPL", quantity=10, average_entry_price=80.00
    )
    db_session.add(position)
    await db_session.commit()

    # 3. Execute BUY payload of 10 shares at $100.0
    payload = PaperExecutionRequest(
        proposal_id=uuid.uuid4(),
        execution_id="EXE-BUY-MERGE",
        portfolio_id=portfolio_id,
        user_id=user_id,
        symbol="AAPL",
        action="BUY",
        requested_quantity=10,
        stop_loss=70.0,
        take_profit=120.0,
        primary_strategy="EMACrossover",
    )

    res = await execution_service.execute_paper_trade(db_session, payload)
    assert res.execution_price == 100.00
    assert res.filled_quantity == 10

    # 4. Verify merged position in DB:
    # new_quantity = 10 + 10 = 20
    # average_entry_price = (10 * 80.0 + 10 * 100.0) / 20 = 90.00
    db_session.expire_all()
    stmt = select(PaperPosition).where(
        PaperPosition.portfolio_id == portfolio_id, PaperPosition.symbol == "AAPL"
    )
    merged_pos = (await db_session.execute(stmt)).scalar_one()

    assert merged_pos.quantity == 20
    assert float(merged_pos.average_entry_price) == 90.00


@pytest.mark.asyncio
@patch("market_service.services.yfinance_service.YFinanceService.get_stock_quote")
async def test_db_sell_reduces_existing_position(
    mock_quote, db_session, execution_service
) -> None:
    """4. SELL reduces existing position quantity"""
    mock_quote.return_value = StockQuote(
        symbol="TSLA", current_price=250.00, change=0, percent_change=0
    )

    user_id = uuid.uuid4()
    portfolio_id = uuid.uuid4()
    portfolio = Portfolio(id=portfolio_id, user_id=user_id, name="Active Portfolio")
    db_session.add(portfolio)

    # Existing position: 15 shares at $200.0
    position = PaperPosition(
        portfolio_id=portfolio_id,
        symbol="TSLA",
        quantity=15,
        average_entry_price=200.00,
    )
    db_session.add(position)
    await db_session.commit()

    # SELL 5 shares
    payload = PaperExecutionRequest(
        proposal_id=uuid.uuid4(),
        execution_id="EXE-SELL-REDUCE",
        portfolio_id=portfolio_id,
        user_id=user_id,
        symbol="TSLA",
        action="SELL",
        requested_quantity=5,
        stop_loss=220.0,
        take_profit=180.0,
        primary_strategy="MeanReversion",
    )

    res = await execution_service.execute_paper_trade(db_session, payload)
    assert res.filled_quantity == 5

    db_session.expire_all()
    stmt = select(PaperPosition).where(
        PaperPosition.portfolio_id == portfolio_id, PaperPosition.symbol == "TSLA"
    )
    updated_pos = (await db_session.execute(stmt)).scalar_one()

    assert updated_pos.quantity == 10
    assert float(updated_pos.average_entry_price) == 200.00  # price remains unchanged


@pytest.mark.asyncio
@patch("market_service.services.yfinance_service.YFinanceService.get_stock_quote")
async def test_db_sell_closes_position_exactly_at_zero(
    mock_quote, db_session, execution_service
) -> None:
    """5. SELL closes position exactly at zero (deletes position row)"""
    mock_quote.return_value = StockQuote(
        symbol="TSLA", current_price=250.00, change=0, percent_change=0
    )

    user_id = uuid.uuid4()
    portfolio_id = uuid.uuid4()
    portfolio = Portfolio(id=portfolio_id, user_id=user_id, name="Active Portfolio")
    db_session.add(portfolio)

    # Existing position: 5 shares
    position = PaperPosition(
        portfolio_id=portfolio_id, symbol="TSLA", quantity=5, average_entry_price=200.00
    )
    db_session.add(position)
    await db_session.commit()

    # SELL 5 shares (exactly matches quantity)
    payload = PaperExecutionRequest(
        proposal_id=uuid.uuid4(),
        execution_id="EXE-SELL-ZERO",
        portfolio_id=portfolio_id,
        user_id=user_id,
        symbol="TSLA",
        action="SELL",
        requested_quantity=5,
        stop_loss=220.0,
        take_profit=180.0,
        primary_strategy="MeanReversion",
    )

    res = await execution_service.execute_paper_trade(db_session, payload)
    assert res.filled_quantity == 5

    db_session.expire_all()
    stmt = select(PaperPosition).where(
        PaperPosition.portfolio_id == portfolio_id, PaperPosition.symbol == "TSLA"
    )
    updated_pos = (await db_session.execute(stmt)).scalar_one_or_none()

    assert updated_pos is None  # Row must be deleted


@pytest.mark.asyncio
@patch("market_service.services.yfinance_service.YFinanceService.get_stock_quote")
async def test_db_sell_without_position_rejected(
    mock_quote, db_session, execution_service
) -> None:
    """6. SELL without position is rejected"""
    mock_quote.return_value = StockQuote(
        symbol="MSFT", current_price=400.00, change=0, percent_change=0
    )

    user_id = uuid.uuid4()
    portfolio_id = uuid.uuid4()
    portfolio = Portfolio(id=portfolio_id, user_id=user_id, name="Active Portfolio")
    db_session.add(portfolio)
    await db_session.commit()

    # Attempt to SELL MSFT without having any position
    payload = PaperExecutionRequest(
        proposal_id=uuid.uuid4(),
        execution_id="EXE-SELL-NOPOS",
        portfolio_id=portfolio_id,
        user_id=user_id,
        symbol="MSFT",
        action="SELL",
        requested_quantity=10,
        stop_loss=410.0,
        take_profit=380.0,
        primary_strategy="EMACrossover",
    )

    with pytest.raises(UnprocessableEntityException) as exc:
        await execution_service.execute_paper_trade(db_session, payload)
    assert "requires an existing" in exc.value.detail


@pytest.mark.asyncio
@patch("market_service.services.yfinance_service.YFinanceService.get_stock_quote")
async def test_db_sell_exceeding_position_quantity_rejected(
    mock_quote, db_session, execution_service
) -> None:
    """7. SELL exceeding position quantity is rejected"""
    mock_quote.return_value = StockQuote(
        symbol="MSFT", current_price=400.00, change=0, percent_change=0
    )

    user_id = uuid.uuid4()
    portfolio_id = uuid.uuid4()
    portfolio = Portfolio(id=portfolio_id, user_id=user_id, name="Active Portfolio")
    db_session.add(portfolio)
    position = PaperPosition(
        portfolio_id=portfolio_id, symbol="MSFT", quantity=5, average_entry_price=400.00
    )
    db_session.add(position)
    await db_session.commit()

    # Attempt to SELL 10 shares when we only have 5
    payload = PaperExecutionRequest(
        proposal_id=uuid.uuid4(),
        execution_id="EXE-SELL-OVERSELL",
        portfolio_id=portfolio_id,
        user_id=user_id,
        symbol="MSFT",
        action="SELL",
        requested_quantity=10,
        stop_loss=410.0,
        take_profit=380.0,
        primary_strategy="EMACrossover",
    )

    with pytest.raises(UnprocessableEntityException) as exc:
        await execution_service.execute_paper_trade(db_session, payload)
    assert "available quantity" in exc.value.detail


# ─────────────────────────────────────────────────────────────────────────────
# API / ROUTER TESTS (Using client AsyncClient)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("market_service.services.yfinance_service.YFinanceService.get_stock_quote")
async def test_api_requires_internal_secret(mock_quote, client, db_session) -> None:
    """19. Internal endpoint requires X-Internal-Secret"""
    mock_quote.return_value = StockQuote(
        symbol="AAPL", current_price=175.50, change=0, percent_change=0
    )

    payload = {
        "proposal_id": str(uuid.uuid4()),
        "execution_id": "EXE-API-NOSECRET",
        "portfolio_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "symbol": "AAPL",
        "action": "BUY",
        "requested_quantity": 10,
        "stop_loss": 170.0,
        "take_profit": 190.0,
        "primary_strategy": "EMACrossover",
    }

    # Request without header
    response = await client.post("/internal/paper-executions", json=payload)
    assert response.status_code == 401
    assert "Missing internal secret" in response.json()["detail"]


@pytest.mark.asyncio
@patch("market_service.services.yfinance_service.YFinanceService.get_stock_quote")
async def test_api_incorrect_secret_rejected(mock_quote, client, db_session) -> None:
    """20. Incorrect internal secret is rejected"""
    mock_quote.return_value = StockQuote(
        symbol="AAPL", current_price=175.50, change=0, percent_change=0
    )

    payload = {
        "proposal_id": str(uuid.uuid4()),
        "execution_id": "EXE-API-WRONGSECRET",
        "portfolio_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "symbol": "AAPL",
        "action": "BUY",
        "requested_quantity": 10,
        "stop_loss": 170.0,
        "take_profit": 190.0,
        "primary_strategy": "EMACrossover",
    }

    # Request with incorrect header
    response = await client.post(
        "/internal/paper-executions",
        json=payload,
        headers={"X-Internal-Secret": "wrong-secret-value"},
    )
    assert response.status_code == 403
    assert "Incorrect internal secret" in response.json()["detail"]


@pytest.mark.asyncio
@patch("market_service.services.yfinance_service.YFinanceService.get_stock_quote")
async def test_api_successful_execution(mock_quote, client, db_session) -> None:
    """14, 15 & 16. API successful execution, price is fetched, quantity is filled and execution is persisted"""
    mock_quote.return_value = StockQuote(
        symbol="AAPL", current_price=180.00, change=0, percent_change=0
    )

    user_id = uuid.uuid4()
    portfolio_id = uuid.uuid4()
    portfolio = Portfolio(id=portfolio_id, user_id=user_id, name="API Portfolio")
    db_session.add(portfolio)
    await db_session.commit()

    proposal_id = uuid.uuid4()
    payload = {
        "proposal_id": str(proposal_id),
        "execution_id": "EXE-API-SUCCESS",
        "portfolio_id": str(portfolio_id),
        "user_id": str(user_id),
        "symbol": "AAPL",
        "action": "BUY",
        "requested_quantity": 10,
        "stop_loss": 170.0,
        "take_profit": 190.0,
        "primary_strategy": "EMACrossover",
    }

    settings = get_settings()
    secret = settings.market_service_internal_secret.get_secret_value()

    response = await client.post(
        "/internal/paper-executions",
        json=payload,
        headers={"X-Internal-Secret": secret},
    )
    assert response.status_code == 201

    data = response.json()
    assert data["execution_id"] == "EXE-API-SUCCESS"
    assert data["filled_quantity"] == 10
    assert data["execution_price"] == 180.00

    # Verify execution details saved in DB
    db_session.expire_all()
    stmt = select(PaperTradeExecution).where(
        PaperTradeExecution.proposal_id == proposal_id
    )
    db_exec = (await db_session.execute(stmt)).scalar_one()

    assert db_exec.execution_id == "EXE-API-SUCCESS"
    assert float(db_exec.execution_price) == 180.00
    assert db_exec.filled_quantity == 10


@pytest.mark.asyncio
@patch("market_service.services.yfinance_service.YFinanceService.get_stock_quote")
async def test_db_transaction_rollback_on_position_failure(
    mock_quote, db_session, execution_service
) -> None:
    """17 & 18. Position and Execution are atomic, and rollback happens on position failure"""
    # Force YFinance quote to fail, causing execute_paper_trade to fail
    mock_quote.return_value = None  # None causes validation failure

    user_id = uuid.uuid4()
    portfolio_id = uuid.uuid4()
    portfolio = Portfolio(id=portfolio_id, user_id=user_id, name="Rollback Portfolio")
    db_session.add(portfolio)
    await db_session.commit()

    proposal_id = uuid.uuid4()
    payload = PaperExecutionRequest(
        proposal_id=proposal_id,
        execution_id="EXE-API-ROLLBACK",
        portfolio_id=portfolio_id,
        user_id=user_id,
        symbol="AAPL",
        action="BUY",
        requested_quantity=10,
        stop_loss=170.0,
        take_profit=190.0,
        primary_strategy="EMACrossover",
    )

    with pytest.raises(UnprocessableEntityException):
        await execution_service.execute_paper_trade(db_session, payload)

    # Verify that NO execution record was committed in the DB
    db_session.expire_all()
    stmt = select(PaperTradeExecution).where(
        PaperTradeExecution.proposal_id == proposal_id
    )
    db_exec = (await db_session.execute(stmt)).scalar_one_or_none()
    assert db_exec is None

    # Verify that NO position record was created
    stmt_pos = select(PaperPosition).where(
        PaperPosition.portfolio_id == portfolio_id, PaperPosition.symbol == "AAPL"
    )
    db_pos = (await db_session.execute(stmt_pos)).scalar_one_or_none()
    assert db_pos is None
