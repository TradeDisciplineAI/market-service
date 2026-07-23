from pydantic import BaseModel


class StockQuote(BaseModel):
    symbol: str
    current_price: float
    change: float | None = None
    percent_change: float | None = None
    previous_close: float | None = None
    currency: str = "USD"
