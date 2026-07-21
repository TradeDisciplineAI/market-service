from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from market_service.schemas.gainers import GainerStock
from market_service.schemas.stock import StockQuote


@pytest.mark.asyncio
async def test_get_stock_quote(client: AsyncClient) -> None:
    mock_quote = StockQuote(
        symbol="AAPL",
        current_price=180.5,
        change=2.5,
        percent_change=1.4,
        previous_close=178.0,
        currency="USD",
    )
    with patch(
        "market_service.routers.dashboard.service.get_stock_quote",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = mock_quote
        response = await client.get("/dashboard/quote/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["current_price"] == 180.5


@pytest.mark.asyncio
async def test_get_gainers(client: AsyncClient) -> None:
    mock_gainers = [
        GainerStock(symbol="NVDA", price=120.0, percent_change=5.5, currency="USD")
    ]
    with patch(
        "market_service.routers.dashboard.service.get_gainers",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = mock_gainers
        response = await client.get("/dashboard/gainers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "NVDA"


@pytest.mark.asyncio
async def test_get_market_analysis(client: AsyncClient) -> None:
    mock_analysis = {
        "gainers": [{"symbol": "NVDA", "price": 120.0, "percent_change": 5.5}],
        "losers": [],
        "last_updated": "2026-07-21T10:00:00Z",
    }
    with patch(
        "market_service.routers.dashboard.get_market_analysis",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = mock_analysis
        response = await client.get("/dashboard/analysis")
        assert response.status_code == 200
        data = response.json()
        assert "gainers" in data
