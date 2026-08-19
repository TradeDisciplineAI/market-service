from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class PaperExecutionRequest(BaseModel):
    """Payload sent from AI-Service to market-service internal endpoint."""

    proposal_id: UUID
    execution_id: str = Field(..., max_length=20)
    portfolio_id: UUID
    user_id: UUID
    symbol: str = Field(..., max_length=20)
    action: str = Field(..., max_length=10)  # "BUY" | "SELL"
    requested_quantity: int = Field(..., gt=0)
    stop_loss: float
    take_profit: float
    primary_strategy: str = Field(..., max_length=100)


class PaperExecutionResponse(BaseModel):
    """Response returned to AI-Service after execution."""

    execution_id: str
    proposal_id: UUID
    symbol: str
    action: str
    filled_quantity: int
    execution_price: float
    executed_at: datetime

    model_config = {"from_attributes": True}
