from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from market_service.schemas.stock import StockSearchResult


@pytest.mark.asyncio
async def test_search_stocks_endpoint(client: AsyncClient) -> None:
    mock_results = [
        StockSearchResult(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            quote_type="EQUITY",
        ),
        StockSearchResult(
            symbol="APLE",
            name="Apple Hospitality REIT, Inc.",
            exchange="NYSE",
            quote_type="EQUITY",
        ),
    ]

    with patch(
        "market_service.routers.dashboard.service.search_stocks",
        new_callable=AsyncMock,
    ) as mock_search:
        mock_search.return_value = mock_results
        response = await client.get("/dashboard/search?q=Apple")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["symbol"] == "AAPL"
        assert data[0]["name"] == "Apple Inc."
        mock_search.assert_called_once_with("Apple")


@pytest.mark.asyncio
async def test_search_stocks_empty_query(client: AsyncClient) -> None:
    response = await client.get("/dashboard/search?q=")
    assert response.status_code == 422  # Validation error for min_length=1
