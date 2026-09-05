import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from httpx import AsyncClient

from market_service.core.config import get_settings
from market_service.models.price_alert import PriceAlert

settings = get_settings()


def create_test_token(user_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "exp": now + timedelta(minutes=15),
        "iat": now,
        "type": "access",
    }
    return jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


@pytest.mark.asyncio
async def test_create_price_alert_unauthorized(client: AsyncClient) -> None:
    response = await client.post(
        "/portfolio/alerts",
        json={"symbol": "TSLA", "target_price": 400.0, "condition": "ABOVE"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_price_alert_success(client: AsyncClient) -> None:
    user_id = str(uuid.uuid4())
    token = create_test_token(user_id)

    mock_alert = PriceAlert(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        symbol="TSLA",
        target_price=400.0,
        condition="ABOVE",
        is_triggered=False,
        created_at=datetime.now(UTC),
    )

    with (
        patch(
            "market_service.routers.alerts.service.repository.count_active_user_alerts",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "market_service.routers.alerts.service.repository.create_alert",
            new_callable=AsyncMock,
            return_value=mock_alert,
        ),
    ):
        response = await client.post(
            "/portfolio/alerts",
            headers={"Authorization": f"Bearer {token}"},
            json={"symbol": "TSLA", "target_price": 400.0, "condition": "ABOVE"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "TSLA"
        assert data["target_price"] == 400.0
        assert data["condition"] == "ABOVE"
        assert data["is_triggered"] is False


@pytest.mark.asyncio
async def test_create_price_alert_limit_exceeded(client: AsyncClient) -> None:
    user_id = str(uuid.uuid4())
    token = create_test_token(user_id)

    with patch(
        "market_service.routers.alerts.service.repository.count_active_user_alerts",
        new_callable=AsyncMock,
        return_value=10,
    ):
        response = await client.post(
            "/portfolio/alerts",
            headers={"Authorization": f"Bearer {token}"},
            json={"symbol": "TSLA", "target_price": 400.0, "condition": "ABOVE"},
        )
        assert response.status_code == 400
        assert "Maximum limit" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_alerts_success(client: AsyncClient) -> None:
    user_id = str(uuid.uuid4())
    token = create_test_token(user_id)

    mock_alerts = [
        PriceAlert(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            symbol="TSLA",
            target_price=400.0,
            condition="ABOVE",
            is_triggered=False,
            created_at=datetime.now(UTC),
        )
    ]

    with patch(
        "market_service.routers.alerts.service.repository.get_user_alerts",
        new_callable=AsyncMock,
        return_value=mock_alerts,
    ):
        response = await client.get(
            "/portfolio/alerts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["symbol"] == "TSLA"


@pytest.mark.asyncio
async def test_delete_alert_success(client: AsyncClient) -> None:
    user_id = str(uuid.uuid4())
    token = create_test_token(user_id)
    alert_id = uuid.uuid4()

    mock_alert = PriceAlert(
        id=alert_id,
        user_id=uuid.UUID(user_id),
        symbol="TSLA",
        target_price=400.0,
        condition="ABOVE",
        is_triggered=False,
        created_at=datetime.now(UTC),
    )

    with (
        patch(
            "market_service.routers.alerts.service.repository.get_alert_by_id",
            new_callable=AsyncMock,
            return_value=mock_alert,
        ),
        patch(
            "market_service.routers.alerts.service.repository.delete_alert",
            new_callable=AsyncMock,
        ),
    ):
        response = await client.delete(
            f"/portfolio/alerts/{alert_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204
