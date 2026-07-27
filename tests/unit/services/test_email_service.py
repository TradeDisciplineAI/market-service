from unittest.mock import AsyncMock, patch

import pytest

from market_service.services.email_service import EmailService


@pytest.mark.asyncio
async def test_send_price_alert_email_skipped_when_no_api_key() -> None:
    with patch(
        "market_service.services.email_service.settings.resend_api_key",
        new=None,
    ):
        result = await EmailService.send_price_alert_email(
            to="trader@example.com",
            symbol="TSLA",
            target_price=400.0,
            condition="ABOVE",
            current_price=402.5,
        )
        assert result is False


@pytest.mark.asyncio
async def test_send_price_alert_email_success() -> None:
    from pydantic import SecretStr

    with (
        patch(
            "market_service.services.email_service.settings.resend_api_key",
            new=SecretStr("re_123456789"),
        ),
        patch(
            "resend.Emails.send_async",
            new_callable=AsyncMock,
            return_value={"id": "msg_123"},
        ) as mock_send,
    ):
        result = await EmailService.send_price_alert_email(
            to="trader@example.com",
            symbol="AAPL",
            target_price=300.0,
            condition="ABOVE",
            current_price=305.0,
        )
        assert result is True
        mock_send.assert_called_once()
