import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from market_service.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from market_service.models.price_alert import PriceAlert
from market_service.schemas.price_alert import AlertCondition, PriceAlertCreate
from market_service.services.price_alert_service import PriceAlertService


@pytest.fixture
def service() -> PriceAlertService:
    return PriceAlertService()


@pytest.mark.asyncio
async def test_create_alert_empty_symbol_raises_bad_request(
    service: PriceAlertService, db_session: AsyncSession
) -> None:
    user_id = uuid.uuid4()
    alert_in = PriceAlertCreate(
        symbol="   ", target_price=100.0, condition=AlertCondition.ABOVE
    )

    with pytest.raises(BadRequestException, match="symbol cannot be empty"):
        await service.create_alert(db_session, user_id, alert_in)


@pytest.mark.asyncio
async def test_delete_alert_not_found_raises_not_found(
    service: PriceAlertService, db_session: AsyncSession
) -> None:
    user_id = uuid.uuid4()
    alert_id = uuid.uuid4()

    with (
        patch.object(
            service.repository,
            "get_alert_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ),
        pytest.raises(NotFoundException, match="Price alert not found"),
    ):
        await service.delete_alert(db_session, user_id, alert_id)


@pytest.mark.asyncio
async def test_delete_alert_forbidden_raises_forbidden(
    service: PriceAlertService, db_session: AsyncSession
) -> None:
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    alert_id = uuid.uuid4()

    mock_alert = PriceAlert(
        id=alert_id,
        user_id=other_user_id,
        symbol="AAPL",
        target_price=300.0,
        condition="ABOVE",
        is_triggered=False,
    )

    with (
        patch.object(
            service.repository,
            "get_alert_by_id",
            new_callable=AsyncMock,
            return_value=mock_alert,
        ),
        pytest.raises(ForbiddenException, match="permission to delete"),
    ):
        await service.delete_alert(db_session, user_id, alert_id)


@pytest.mark.asyncio
async def test_evaluate_price_change_triggers_above_and_below(
    service: PriceAlertService, db_session: AsyncSession
) -> None:
    symbol = "TSLA"

    alert_above = PriceAlert(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        symbol=symbol,
        target_price=400.0,
        condition="ABOVE",
        is_triggered=False,
        created_at=datetime.now(UTC),
    )

    alert_below = PriceAlert(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        symbol=symbol,
        target_price=350.0,
        condition="BELOW",
        is_triggered=False,
        created_at=datetime.now(UTC),
    )

    with (
        patch.object(
            service.repository,
            "get_active_alerts_by_symbol",
            new_callable=AsyncMock,
            return_value=[alert_above, alert_below],
        ),
        patch.object(
            service.repository,
            "mark_triggered",
            new_callable=AsyncMock,
        ) as mock_mark,
    ):
        # Test AAPL price at 405.0 -> should trigger alert_above
        triggered = await service.evaluate_price_change(
            db_session, symbol, current_price=405.0
        )
        assert len(triggered) == 1
        assert triggered[0] == alert_above
        mock_mark.assert_called_once_with(db_session, [alert_above])
