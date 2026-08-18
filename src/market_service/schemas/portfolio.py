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


class PaperPositionCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    quantity: int = Field(..., gt=0)
    average_entry_price: float = Field(..., gt=0.0)


class PaperPositionResponse(BaseModel):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    symbol: str
    quantity: int
    average_entry_price: float
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class PortfolioCreate(BaseModel):
    name: str = Field(default="My Paper Portfolio", min_length=1, max_length=100)
    type: str = Field(default="PAPER")


class PortfolioResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: str = "PAPER"
    holdings: list[PortfolioHoldingResponse] = Field(default_factory=list)
    positions: list[PaperPositionResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }
