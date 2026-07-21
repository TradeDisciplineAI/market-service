import json
import logging
from datetime import UTC, datetime
from typing import Any, cast

import redis.asyncio as redis

from market_service.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def get_redis_client() -> redis.Redis:
    """Return a fresh async Redis client for explicit lifecycle management."""
    return redis.from_url(settings.redis_url, decode_responses=True)


async def save_market_data(
    symbol: str,
    data: dict[str, Any],
    client: redis.Redis | None = None,
) -> None:
    r = client or redis_client
    await r.set(
        f"market:{symbol}",
        json.dumps(data),
    )


async def get_market_data(
    symbol: str,
    client: redis.Redis | None = None,
) -> dict[str, Any] | None:
    r = client or redis_client
    data = await r.get(f"market:{symbol}")
    if data:
        return cast(dict[str, Any], json.loads(data))
    return None


async def save_market_analysis(
    gainers: list[Any],
    losers: list[Any],
    client: redis.Redis | None = None,
) -> None:
    r = client or redis_client
    await r.set(
        "market:analysis",
        json.dumps(
            {
                "gainers": gainers,
                "losers": losers,
                "last_updated": datetime.now(UTC).isoformat(),
            }
        ),
    )


async def get_market_analysis(
    client: redis.Redis | None = None,
) -> dict[str, Any]:
    r = client or redis_client
    data = await r.get("market:analysis")
    if data:
        try:
            return cast(dict[str, Any], json.loads(data))
        except Exception:
            logger.exception("Failed to parse market analysis from Redis")
    return {"gainers": [], "losers": [], "last_updated": None}
