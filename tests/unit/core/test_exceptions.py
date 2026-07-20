from market_service.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
    UnauthorizedException,
    UnprocessableEntityException,
)


def test_exception_status_codes() -> None:
    assert BadRequestException().status_code == 400
    assert UnauthorizedException().status_code == 401
    assert ForbiddenException().status_code == 403
    assert NotFoundException().status_code == 404
    assert ConflictException().status_code == 409
    assert UnprocessableEntityException().status_code == 422
    assert InternalServerException().status_code == 500
