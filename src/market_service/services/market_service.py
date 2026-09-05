import logging
import random
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


def generate_market_price(symbol: str) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "price": round(random.uniform(400, 500), 2),  # noqa: S311
        "timestamp": datetime.now(UTC).isoformat(),
    }
