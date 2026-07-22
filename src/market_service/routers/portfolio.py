from fastapi import APIRouter, status

from market_service.core.dependencies import CurrentUserDep, DbDep
from market_service.models.portfolio import Portfolio
from market_service.models.portfolio_holding import PortfolioHolding
from market_service.schemas.portfolio import (
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
    portfolio_in: PortfolioCreate,
) -> Portfolio:
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
) -> Portfolio:
    return await service.get_portfolio(db, current_user.user_id)


@router.post(
    "/holdings",
    response_model=PortfolioHoldingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_holding(
    db: DbDep,
    current_user: CurrentUserDep,
    holding_in: PortfolioHoldingCreate,
) -> PortfolioHolding:
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
