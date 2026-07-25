import asyncio
import logging
from contextlib import suppress

import yfinance as yf

with suppress(Exception):
    yf.set_tz_cache_location("/tmp/py-yfinance")  # noqa: S108

import httpx

from market_service.schemas.gainers import GainerStock
from market_service.schemas.stock import (
    StockQuote,
    StockSearchResult,
    TradingViewCandle,
)

logger = logging.getLogger(__name__)


class YFinanceService:
    WATCHLIST = [
        # Indian Stocks (NSE)
        "RELIANCE.NS",
        "TCS.NS",
        "HDFCBANK.NS",
        "INFY.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "BHARTIARTL.NS",
        "ITC.NS",
        "LT.NS",
        "BAJFINANCE.NS",
        "AXISBANK.NS",
        "KOTAKBANK.NS",
        "HCLTECH.NS",
        "MARUTI.NS",
        "SUNPHARMA.NS",
        "HINDUNILVR.NS",
        "M&M.NS",
        "TATASTEEL.NS",
        "ASIANPAINT.NS",
        "WIPRO.NS",
        # US Stocks
        "AAPL",
        "MSFT",
        "NVDA",
        "TSLA",
        "META",
        "GOOGL",
        "AMZN",
        "AMD",
        "NFLX",
        "COIN",
    ]

    def __init__(self) -> None:
        pass

    def _fetch_quote_sync(self, symbol: str) -> StockQuote:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info

        current_price = info.last_price
        previous_close = info.previous_close

        change = current_price - previous_close if previous_close else 0.0
        percent_change = (change / previous_close) * 100 if previous_close else 0.0

        return StockQuote(
            symbol=symbol,
            current_price=current_price,
            change=change,
            percent_change=percent_change,
            high=getattr(info, "day_high", None),
            low=getattr(info, "day_low", None),
            open_price=getattr(info, "open", None),
            previous_close=previous_close,
            currency=getattr(info, "currency", "USD"),
        )

    async def get_stock_quote(self, symbol: str) -> StockQuote | None:
        try:
            return await asyncio.to_thread(self._fetch_quote_sync, symbol)
        except Exception:
            logger.exception("Failed to fetch quote data for %s", symbol)
            return None

    def _fetch_historical_sync(self, symbol: str, period: str = "1mo") -> list[TradingViewCandle]:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period)
        
        candles = []
        for date, row in history.iterrows():
            time_str = date.strftime("%Y-%m-%d")
            candles.append(
                TradingViewCandle(
                    time=time_str,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                )
            )
        return candles

    async def get_historical_data(self, symbol: str, period: str = "1mo") -> list[TradingViewCandle]:
        try:
            return await asyncio.to_thread(self._fetch_historical_sync, symbol, period)
        except Exception:
            logger.exception("Failed to fetch historical data for %s", symbol)
            return []

    def _fetch_gainers_sync(self) -> list[GainerStock]:
        gainers = []
        for symbol in self.WATCHLIST:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.fast_info
                current_price = info.last_price
                previous_close = info.previous_close
                change = current_price - previous_close if previous_close else 0.0
                percent_change = (
                    (change / previous_close) * 100 if previous_close else 0.0
                )

                gainers.append(
                    GainerStock(
                        symbol=symbol,
                        price=current_price,
                        percent_change=percent_change,
                    )
                )
            except Exception:
                logger.exception("Failed to fetch gainer data for %s", symbol)

        gainers.sort(key=lambda stock: stock.percent_change, reverse=True)
        return gainers[:15]

    async def get_gainers(self) -> list[GainerStock]:
        return await asyncio.to_thread(self._fetch_gainers_sync)

    async def search_stocks(self, query: str) -> list[StockSearchResult]:
        """Search Yahoo Finance for stock symbols matching the search query."""
        clean_query = query.strip()
        if not clean_query:
            return []

        headers = {"User-Agent": "Mozilla/5.0"}
        params: dict[str, str] = {"q": clean_query, "quotesCount": "10"}

        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    "https://query2.finance.yahoo.com/v1/finance/search",
                    params=params,
                    headers=headers,
                    timeout=5.0,
                )
                if res.status_code != 200:
                    logger.warning("Yahoo search API status %s", res.status_code)
                    return []

                data = res.json()
                results = []
                for item in data.get("quotes", []):
                    symbol = item.get("symbol")
                    name = item.get("shortname") or item.get("longname") or symbol
                    if symbol:
                        results.append(
                            StockSearchResult(
                                symbol=symbol,
                                name=name,
                                exchange=item.get("exchDisp") or item.get("exchange"),
                                quote_type=item.get("quoteType"),
                            )
                        )
                return results
        except Exception:
            logger.exception("Failed to search stocks for query: %s", query)
            return []
