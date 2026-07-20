"""Stateless JWT access token verification utility."""

from __future__ import annotations

from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError

from .config import get_settings

settings = get_settings()


def decode_access_token(
    token: str,
) -> dict[str, Any] | None:
    """Verify and decode an incoming JWT access token statelessly."""

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
        )

        if payload.get("type") != "access":
            return None

        return payload

    except InvalidTokenError:
        return None
