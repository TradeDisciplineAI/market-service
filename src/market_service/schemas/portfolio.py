import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PortfolioHoldingCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)


class PortfolioHoldingResponse(BaseModel):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    symbol: str
    created_at: datetime
    price: float | None = None
    percent_change: float | None = None
    currency: str | None = None

    model_config = {
        "from_attributes": True,
    }


class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class PortfolioResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    holdings: list[PortfolioHoldingResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }
