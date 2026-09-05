import uuid

from fastapi import APIRouter, status

from market_service.core.dependencies import CurrentUserDep, DbDep
from market_service.schemas.price_alert import (
    PriceAlertCreate,
    PriceAlertListResponse,
    PriceAlertResponse,
)
from market_service.services.price_alert_service import PriceAlertService

router = APIRouter(
    prefix="/portfolio/alerts",
    tags=["Price Alerts"],
)

service = PriceAlertService()


@router.post(
    "",
    response_model=PriceAlertResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_alert(
    db: DbDep,
    current_user: CurrentUserDep,
    alert_in: PriceAlertCreate,
) -> PriceAlertResponse:
    return await service.create_alert(
        db=db,
        user_id=current_user.user_id,
        alert_in=alert_in,
    )


@router.get(
    "",
    response_model=PriceAlertListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_alerts(
    db: DbDep,
    current_user: CurrentUserDep,
) -> PriceAlertListResponse:
    return await service.get_user_alerts(
        db=db,
        user_id=current_user.user_id,
    )


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_alert(
    db: DbDep,
    current_user: CurrentUserDep,
    alert_id: uuid.UUID,
) -> None:
    await service.delete_alert(
        db=db,
        user_id=current_user.user_id,
        alert_id=alert_id,
    )
