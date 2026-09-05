import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from market_service.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from market_service.models.price_alert import PriceAlert
from market_service.repositories.price_alert_repository import PriceAlertRepository
from market_service.schemas.price_alert import (
    PriceAlertCreate,
    PriceAlertListResponse,
    PriceAlertResponse,
)

logger = logging.getLogger(__name__)

MAX_ALERTS_PER_USER = 10


class PriceAlertService:
    def __init__(self) -> None:
        self.repository = PriceAlertRepository()

    async def create_alert(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        alert_in: PriceAlertCreate,
    ) -> PriceAlertResponse:
        symbol = alert_in.symbol.strip().upper()
        if not symbol:
            raise BadRequestException("Stock symbol cannot be empty")

        if alert_in.target_price <= 0:
            raise BadRequestException("Target price must be greater than zero")

        active_count = await self.repository.count_active_user_alerts(db, user_id)
        if active_count >= MAX_ALERTS_PER_USER:
            raise BadRequestException(
                f"Maximum limit of {MAX_ALERTS_PER_USER} active alerts reached"
            )

        alert = PriceAlert(
            user_id=user_id,
            symbol=symbol,
            target_price=alert_in.target_price,
            condition=alert_in.condition.value,
            is_triggered=False,
        )
        created_alert = await self.repository.create_alert(db, alert)
        return PriceAlertResponse.model_validate(created_alert)

    async def get_user_alerts(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> PriceAlertListResponse:
        alerts = await self.repository.get_user_alerts(db, user_id)
        items = [PriceAlertResponse.model_validate(a) for a in alerts]
        return PriceAlertListResponse(items=items, total=len(items))

    async def delete_alert(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        alert_id: uuid.UUID,
    ) -> None:
        alert = await self.repository.get_alert_by_id(db, alert_id)
        if not alert:
            raise NotFoundException("Price alert not found")

        if alert.user_id != user_id:
            raise ForbiddenException("You do not have permission to delete this alert")

        await self.repository.delete_alert(db, alert)

    async def evaluate_price_change(
        self,
        db: AsyncSession,
        symbol: str,
        current_price: float,
    ) -> list[PriceAlert]:
        """Evaluate symbol's active alerts against incoming price tick."""
        symbol = symbol.strip().upper()
        active_alerts = await self.repository.get_active_alerts_by_symbol(db, symbol)

        triggered_alerts: list[PriceAlert] = []
        for alert in active_alerts:
            hit_above = (
                alert.condition == "ABOVE" and current_price >= alert.target_price
            )
            hit_below = (
                alert.condition == "BELOW" and current_price <= alert.target_price
            )
            if hit_above or hit_below:
                triggered_alerts.append(alert)

        if triggered_alerts:
            await self.repository.mark_triggered(db, triggered_alerts)
            logger.info(
                "Triggered %d price alerts for %s at %s",
                len(triggered_alerts),
                symbol,
                current_price,
            )
            # Dispatch Resend email for each triggered alert asynchronously
            from market_service.services.email_service import EmailService

            for alert in triggered_alerts:
                # Optional: Send to user email if configured
                user_email = getattr(alert, "user_email", None)
                if user_email:
                    await EmailService.send_price_alert_email(
                        to=user_email,
                        symbol=symbol,
                        target_price=alert.target_price,
                        condition=alert.condition,
                        current_price=current_price,
                    )

        return triggered_alerts
