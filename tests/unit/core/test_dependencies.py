import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from market_service.core.config import get_settings
from market_service.core.dependencies import get_current_user
from market_service.core.exceptions import UnauthorizedException

settings = get_settings()


@pytest.mark.anyio
async def test_get_current_user_valid_token() -> None:
    user_id = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "exp": datetime.now(UTC) + timedelta(minutes=15),
        "type": "access",
    }
    token = jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )

    user = await get_current_user(token)
    assert user.sub == user_id
    assert str(user.user_id) == user_id


@pytest.mark.anyio
async def test_get_current_user_missing_token() -> None:
    with pytest.raises(UnauthorizedException):
        await get_current_user(None)


@pytest.mark.anyio
async def test_get_current_user_invalid_token() -> None:
    with pytest.raises(UnauthorizedException):
        await get_current_user("invalid.jwt.token")


@pytest.mark.anyio
async def test_get_current_user_invalid_uuid() -> None:
    payload = {
        "sub": "not-a-uuid",
        "exp": datetime.now(UTC) + timedelta(minutes=15),
        "type": "access",
    }
    token = jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )
    with pytest.raises(UnauthorizedException):
        await get_current_user(token)
