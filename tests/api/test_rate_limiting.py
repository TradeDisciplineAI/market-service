import pytest
from httpx import AsyncClient

from market_service.core.config import get_settings

settings = get_settings()


@pytest.mark.anyio
async def test_health_endpoint_response(client: AsyncClient) -> None:
    """Test health endpoint returns status ok and correct version."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == settings.app_version


@pytest.mark.anyio
async def test_root_endpoint_response(client: AsyncClient) -> None:
    """Test root endpoint returns Market Service running message."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Market Service" in data["message"]
