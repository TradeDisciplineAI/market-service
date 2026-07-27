import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AlertCondition(StrEnum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"


class PriceAlertCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    target_price: float = Field(..., gt=0, description="Target trigger price")
    condition: AlertCondition = Field(
        default=AlertCondition.ABOVE,
        description="Condition: ABOVE or BELOW",
    )


class PriceAlertResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    symbol: str
    target_price: float
    condition: AlertCondition
    is_triggered: bool
    created_at: datetime
    triggered_at: datetime | None = None

    model_config = {
        "from_attributes": True,
    }


class PriceAlertListResponse(BaseModel):
    items: list[PriceAlertResponse]
    total: int
