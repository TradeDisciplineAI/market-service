from fastapi import APIRouter, Header, Depends, status

from market_service.core.config import get_settings
from market_service.core.dependencies import DbDep
from market_service.core.exceptions import UnauthorizedException, ForbiddenException
from market_service.schemas.execution import (
    PaperExecutionRequest,
    PaperExecutionResponse,
)
from market_service.services.execution_service import ExecutionService

router = APIRouter(
    prefix="/internal",
    tags=["Internal Paper Execution"],
)

service = ExecutionService()


async def verify_internal_secret(
    x_internal_secret: str | None = Header(None, alias="X-Internal-Secret"),
) -> None:
    """Validate internal service communication secret."""
    settings = get_settings()
    expected = settings.market_service_internal_secret.get_secret_value()

    if not x_internal_secret:
        raise UnauthorizedException("Missing internal secret header")

    if x_internal_secret != expected:
        raise ForbiddenException("Incorrect internal secret")


@router.post(
    "/paper-executions",
    response_model=PaperExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_internal_secret)],
    summary="Internal endpoint to execute paper trades",
)
async def execute_paper_trade(
    db: DbDep,
    payload: PaperExecutionRequest,
) -> PaperExecutionResponse:
    """
    Executes a paper trade. Accessible only internally via service secret.
    Calculates execution price dynamically using live stock quotes.
    Updates positions atomically.
    """
    return await service.execute_paper_trade(db, payload)
