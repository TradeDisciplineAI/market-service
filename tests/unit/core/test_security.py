from datetime import UTC, datetime, timedelta

import jwt

from market_service.core.config import get_settings
from market_service.core.security import decode_access_token

settings = get_settings()


def test_decode_access_token_valid() -> None:
    # Arrange
    user_id = "12345678-1234-5678-1234-567812345678"
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "exp": now + timedelta(minutes=15),
        "iat": now,
        "type": "access",
    }
    valid_token = jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )

    # Act
    decoded = decode_access_token(valid_token)

    # Assert
    assert decoded is not None
    assert decoded["sub"] == user_id
    assert decoded["type"] == "access"


def test_decode_access_token_invalid_signature() -> None:
    # Arrange
    user_id = "12345678-1234-5678-1234-567812345678"
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "exp": now + timedelta(minutes=15),
        "type": "access",
    }
    valid_token = jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )

    # Act
    decoded = decode_access_token(valid_token + "invalid")

    # Assert
    assert decoded is None


def test_decode_access_token_wrong_type() -> None:
    # Arrange
    user_id = "12345678-1234-5678-1234-567812345678"
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "exp": now + timedelta(minutes=15),
        "type": "refresh",
    }
    refresh_token = jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )

    # Act & Assert
    assert decode_access_token(refresh_token) is None


def test_decode_access_token_expired() -> None:
    # Arrange
    user_id = "12345678-1234-5678-1234-567812345678"
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "exp": now - timedelta(seconds=1),
        "iat": now - timedelta(seconds=10),
        "type": "access",
    }
    expired_token = jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )

    # Act
    decoded = decode_access_token(expired_token)

    # Assert
    assert decoded is None
