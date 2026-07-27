import uuid
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from market_service.models.price_alert import PriceAlert


class PriceAlertRepository:
    async def create_alert(
        self,
        db: AsyncSession,
        alert: PriceAlert,
    ) -> PriceAlert:
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert

    async def get_user_alerts(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[PriceAlert]:
        stmt = (
            select(PriceAlert)
            .where(PriceAlert.user_id == user_id)
            .order_by(PriceAlert.created_at.desc())
        )
        result = await db.execute(stmt)
        return cast(list[PriceAlert], list(result.scalars().all()))

    async def get_alert_by_id(
        self,
        db: AsyncSession,
        alert_id: uuid.UUID,
    ) -> PriceAlert | None:
        stmt = select(PriceAlert).where(PriceAlert.id == alert_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_alert(
        self,
        db: AsyncSession,
        alert: PriceAlert,
    ) -> None:
        await db.delete(alert)
        await db.commit()

    async def count_active_user_alerts(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> int:
        stmt = select(PriceAlert).where(
            PriceAlert.user_id == user_id,
            PriceAlert.is_triggered == False,  # noqa: E712
        )
        result = await db.execute(stmt)
        return len(result.scalars().all())

    async def get_active_alerts_by_symbol(
        self,
        db: AsyncSession,
        symbol: str,
    ) -> list[PriceAlert]:
        stmt = select(PriceAlert).where(
            PriceAlert.symbol == symbol,
            PriceAlert.is_triggered == False,  # noqa: E712
        )
        result = await db.execute(stmt)
        return cast(list[PriceAlert], list(result.scalars().all()))

    async def mark_triggered(
        self,
        db: AsyncSession,
        alerts: list[PriceAlert],
    ) -> None:
        now = datetime.now(UTC)
        for alert in alerts:
            alert.is_triggered = True
            alert.triggered_at = now
        await db.commit()
