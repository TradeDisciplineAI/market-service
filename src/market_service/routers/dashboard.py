import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from market_service.core.redis import get_market_analysis
from market_service.core.websocket_manager import manager
from market_service.schemas.gainers import GainerStock
from market_service.schemas.stock import StockQuote
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
    """Real-time WebSocket endpoint that streams Gainers and Losers."""
    await manager.connect(websocket)
    try:
        # Instantly send the current state upon connection
        await websocket.send_json(await get_market_analysis())

        # Keep connection open infinitely
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
