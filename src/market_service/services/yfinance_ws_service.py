import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from market_service.core.redis import get_market_data, save_market_data
from market_service.services.yfinance_service import YFinanceService

logger = logging.getLogger(__name__)


class YFinanceWebSocketService:
    def __init__(self) -> None:
        self.service = YFinanceService()
        self.symbols = self.service.WATCHLIST

    async def connect_and_listen(self) -> None:
        logger.info(
            "[YFinance WS Sim] Started! Polling %d symbols...",
            len(self.symbols),
        )

        while True:
            try:
                quotes_map = await self._fetch_all_quotes()

                for symbol, quote in quotes_map.items():
                    if not quote:
                        continue
                    new_price = quote.current_price
                    timestamp = datetime.now(UTC).isoformat()

                    existing_data = (await get_market_data(symbol)) or {}
                    existing_data["symbol"] = symbol
                    existing_data["price"] = new_price
                    existing_data["timestamp"] = timestamp
                    existing_data["currency"] = quote.currency

                    await save_market_data(symbol, existing_data)

                # Poll every 10 seconds to avoid Yahoo Finance rate limits
                await asyncio.sleep(10)

            except Exception:
                logger.exception("[YFinance WS Sim] Unexpected Error")
                await asyncio.sleep(5)

    async def _fetch_all_quotes(self) -> dict[str, Any]:
        tasks = [self.service.get_stock_quote(symbol) for symbol in self.symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = {}
        for idx, res in enumerate(results):
            if not isinstance(res, Exception):
                valid_results[self.symbols[idx]] = res
        return valid_results
