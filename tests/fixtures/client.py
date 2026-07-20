from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from market_service.main import app


@pytest.fixture
def fastapi_app() -> FastAPI:
    """Yield the FastAPI application instance."""
    return app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """Yield an AsyncClient for test requests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
