"""Helper utilities for JWT generation and verification in tests."""

from typing import Any


def decode_test_token(token: str) -> dict[str, Any]:
    """Mock/decode helper for test JWT tokens."""
    return {"sub": "test", "token": token}
