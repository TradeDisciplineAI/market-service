"""Email service powered by Resend for Market Service notifications."""

from __future__ import annotations

import html
import logging
from datetime import UTC, datetime

import resend

from market_service.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Async Email service using Resend API."""

    @staticmethod
    async def send_email(
        *,
        to: str,
        subject: str,
        html_body: str,
    ) -> bool:
        """Send an email using Resend API."""
        if not settings.resend_api_key:
            logger.warning(
                "RESEND_API_KEY is not set. Email notification skipped for %s", to
            )
            return False

        try:
            resend.api_key = settings.resend_api_key.get_secret_value()
            await resend.Emails.send_async(
                {
                    "from": settings.email_from,
                    "to": to,
                    "subject": subject,
                    "html": html_body,
                }
            )
            logger.info("Price alert notification email sent to %s", to)
            return True
        except Exception as e:
            logger.error("Failed to send price alert email to %s: %s", to, e)
            return False

    @staticmethod
    async def send_price_alert_email(
        *,
        to: str,
        symbol: str,
        target_price: float,
        condition: str,
        current_price: float,
    ) -> bool:
        """Send Vercel dark HTML email notification when price target alert triggers."""
        escaped_symbol = html.escape(symbol.upper())
        escaped_condition = html.escape(condition.upper())
        formatted_target = f"{target_price:.2f}"
        formatted_current = f"{current_price:.2f}"
        now_str = datetime.now(UTC).strftime("%B %d, %Y at %I:%M %p UTC")
        current_year = datetime.now(UTC).year

        subject = f"🔔 Price Alert: {escaped_symbol} crossed target ${formatted_target}"

        p_text = (
            f"Your custom price alarm for <strong>{escaped_symbol}</strong> "
            "has been triggered on the live market feed."
        )
        condition_text = f"GOES {escaped_condition} ${formatted_target}"

        html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Price Target Alert Triggered</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #000000;
      color: #ededed;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 560px;
      margin: 32px auto;
      background-color: #0a0a0a;
      border: 1px solid #1a1a1a;
      border-radius: 8px;
      padding: 32px;
    }}
    .header {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 24px;
      border-bottom: 1px solid #1a1a1a;
      padding-bottom: 16px;
    }}
    .brand-title {{
      font-size: 18px;
      font-weight: 700;
      color: #ffffff;
      letter-spacing: -0.02em;
    }}
    .alert-badge {{
      display: inline-block;
      background: rgba(0, 229, 153, 0.12);
      border: 1px solid rgba(0, 229, 153, 0.3);
      color: #00e599;
      font-size: 12px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 12px;
      margin-bottom: 16px;
    }}
    .price-card {{
      background: #111111;
      border: 1px solid #222222;
      border-radius: 6px;
      padding: 20px;
      margin: 20px 0;
    }}
    .stock-symbol {{
      font-size: 24px;
      font-weight: 800;
      color: #ffffff;
      font-family: monospace;
    }}
    .price-value {{
      font-size: 28px;
      font-weight: 700;
      color: #00e599;
      margin-top: 8px;
    }}
    .details-row {{
      display: flex;
      justify-content: space-between;
      font-size: 14px;
      color: #888888;
      margin-top: 12px;
      border-top: 1px solid #1f1f1f;
      padding-top: 12px;
    }}
    .btn-container {{
      margin: 28px 0 16px 0;
      text-align: center;
    }}
    .btn {{
      display: inline-block;
      background-color: #ffffff;
      color: #000000 !important;
      font-weight: 600;
      text-decoration: none;
      padding: 12px 24px;
      border-radius: 6px;
      font-size: 14px;
    }}
    .footer {{
      margin-top: 32px;
      border-top: 1px solid #1a1a1a;
      padding-top: 16px;
      font-size: 12px;
      color: #666666;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="brand-title">⚡ AI Trading Discipline Co-Pilot</span>
    </div>

    <div class="alert-badge">🔔 PRICE ALERT TRIGGERED</div>

    <p style="font-size: 15px; color: #ededed; margin: 0;">
      {p_text}
    </p>

    <div class="price-card">
      <div class="stock-symbol">{escaped_symbol}</div>
      <div class="price-value">${formatted_current}</div>
      <div class="details-row">
        <span>Target Condition: <strong>{condition_text}</strong></span>
      </div>
      <div class="details-row">
        <span>Triggered At: <strong>{now_str}</strong></span>
      </div>
    </div>

    <div class="btn-container">
      <a href="http://localhost:3000/#/explore" class="btn" target="_blank">
        View Market Dashboard
      </a>
    </div>

    <div class="footer">
      &copy; {current_year} AI Trading Co-Pilot. All rights reserved.
    </div>
  </div>
</body>
</html>"""

        return await EmailService.send_email(
            to=to,
            subject=subject,
            html_body=html_body,
        )
