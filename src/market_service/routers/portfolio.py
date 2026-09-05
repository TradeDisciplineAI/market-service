import uuid

from fastapi import APIRouter, status

from market_service.core.dependencies import CurrentUserDep, DbDep
from market_service.schemas.portfolio import (
    PaperPositionCreate,
    PaperPositionResponse,
    PortfolioCreate,
    PortfolioHoldingCreate,
    PortfolioHoldingResponse,
    PortfolioResponse,
)
from market_service.services.portfolio_service import PortfolioService

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)

service = PortfolioService()


@router.post(
    "",
    response_model=PortfolioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_portfolio(
    db: DbDep,
    current_user: CurrentUserDep,
    portfolio_in: PortfolioCreate | None = None,
) -> PortfolioResponse:
    if portfolio_in is None:
        portfolio_in = PortfolioCreate()
    return await service.create_portfolio(
        db,
        current_user.user_id,
        portfolio_in,
    )


@router.get(
    "",
    response_model=PortfolioResponse,
)
async def get_portfolio(
    db: DbDep,
    current_user: CurrentUserDep,
) -> PortfolioResponse:
    return await service.get_portfolio(db, current_user.user_id)


@router.get(
    "/{portfolio_id}/positions",
    response_model=list[PaperPositionResponse],
)
async def get_positions(
    portfolio_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUserDep,
) -> list[PaperPositionResponse]:
    return await service.get_positions(db, current_user.user_id, portfolio_id)


@router.post(
    "/{portfolio_id}/positions",
    response_model=PaperPositionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_or_update_position(
    portfolio_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUserDep,
    position_in: PaperPositionCreate,
) -> PaperPositionResponse:
    return await service.add_or_update_position(
        db, current_user.user_id, portfolio_id, position_in
    )


@router.post(
    "/holdings",
    response_model=PortfolioHoldingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_holding(
    db: DbDep,
    current_user: CurrentUserDep,
    holding_in: PortfolioHoldingCreate,
) -> PortfolioHoldingResponse:
    return await service.add_holding(db, current_user.user_id, holding_in)


@router.delete(
    "/holdings/{symbol}",
)
async def remove_holding(
    db: DbDep,
    current_user: CurrentUserDep,
    symbol: str,
) -> dict[str, str]:
    await service.remove_holding(db, current_user.user_id, symbol)
    return {"message": "Holding removed successfully"}
