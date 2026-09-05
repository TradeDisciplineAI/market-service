from pydantic import BaseModel


class StockQuote(BaseModel):
    symbol: str
    current_price: float
    change: float | None = None
    percent_change: float | None = None
    previous_close: float | None = None
    currency: str = "USD"


class StockSearchResult(BaseModel):
    symbol: str
    name: str
    exchange: str | None = None
    quote_type: str | None = None


class TradingViewCandle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float


class StockAnalysisResponse(BaseModel):
    symbol: str
    authorized: bool
    chart_data: list[TradingViewCandle]
    analysis: dict[str, str]


class StockIndicators(BaseModel):
    symbol: str
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
