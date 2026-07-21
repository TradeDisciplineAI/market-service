from pydantic import BaseModel


class GainerStock(BaseModel):
    symbol: str
    price: float
    percent_change: float
    currency: str = "USD"
