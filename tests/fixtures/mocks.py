from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True)
def disable_limiter() -> Generator[None]:
    """Globally disable the slowapi rate limiter for functional tests."""
    from market_service.core.limiter import limiter

    limiter.enabled = False
    yield
    limiter.enabled = True
