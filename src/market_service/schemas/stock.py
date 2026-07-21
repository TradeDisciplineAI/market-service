from pydantic import BaseModel


class StockQuote(BaseModel):
    symbol: str
    current_price: float
    previous_close: float | None = None
    currency: str = "USD"
