import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from market_service.core.dependencies import CurrentUserDep
from market_service.core.redis import get_market_analysis
from market_service.core.websocket_manager import manager
from market_service.schemas.gainers import GainerStock
from market_service.schemas.stock import (
    StockAnalysisResponse,
    StockQuote,
    StockSearchResult,
)
from market_service.services.yfinance_service import YFinanceService

logger = logging.getLogger(__name__)

service = YFinanceService()
router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/quote/{symbol}", response_model=StockQuote)
async def get_stock_quote(symbol: str) -> StockQuote | None:
    return await service.get_stock_quote(symbol)


@router.get("/analyze-stock/{symbol}", response_model=StockAnalysisResponse)
async def analyze_stock(
    symbol: str,
    current_user: CurrentUserDep,
) -> StockAnalysisResponse:
    """Secure endpoint that fetches historical data and formats it for TradingView."""
    chart_data = await service.get_historical_data(symbol, period="1mo")
    
    analysis = {}
    if chart_data:
        latest = chart_data[-1]
        oldest = chart_data[0]
        if latest.close > oldest.close:
            analysis["trend"] = "BULLISH"
            analysis["recommendation"] = "HOLD/BUY"
        else:
            analysis["trend"] = "BEARISH"
            analysis["recommendation"] = "HOLD/SELL"
    else:
        analysis["trend"] = "UNKNOWN"
        analysis["recommendation"] = "NONE"

    return StockAnalysisResponse(
        symbol=symbol.upper(),
        authorized=True,
        chart_data=chart_data,
        analysis=analysis,
    )


@router.get(
    "/search",
    response_model=list[StockSearchResult],
)
async def search_stocks(
    q: str = Query(
        ...,
        min_length=1,
        description="Stock search query (name or ticker)",
    ),
) -> list[StockSearchResult]:
    """Search for stock symbols matching the query string."""
    return await service.search_stocks(q)


@router.get(
    "/gainers",
    response_model=list[GainerStock],
)
async def get_gainers() -> list[GainerStock]:
    return await service.get_gainers()


@router.get("/analysis")
async def get_market_analysis_endpoint() -> dict[str, Any]:
    """Returns the latest Gainers and Losers calculated by the Celery worker."""
    return await get_market_analysis()


@router.websocket("/ws/market")
async def websocket_market_endpoint(websocket: WebSocket) -> None:
    """Real-time WebSocket endpoint that streams Gainers and Losers continuously."""
    await manager.connect(websocket)
    try:
        while True:
            analysis = await get_market_analysis()
            await websocket.send_json(analysis)
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
