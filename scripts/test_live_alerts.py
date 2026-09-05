import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from httpx import ASGITransport, AsyncClient

from market_service.core.config import get_settings
from market_service.core.database import AsyncSessionFactory
from market_service.main import app
from market_service.services.price_alert_service import PriceAlertService

settings = get_settings()


def create_token(user_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "exp": now + timedelta(minutes=15),
        "iat": now,
        "type": "access",
    }
    return jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


async def main() -> None:
    print("=" * 60)
    print("LIVE TESTING ENDPOINTS & PRICE ALARM TRIGGER ENGINE")
    print("=" * 60)

    user_id = str(uuid.uuid4())
    token = create_token(user_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "Host": "localhost",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost",
    ) as client:
        # 1. Health check
        print("\n[1] Testing GET /health...")
        res = await client.get("/health", headers={"Host": "localhost"})
        print(f"    Status: {res.status_code} | Body: {res.json()}")
        assert res.status_code == 200  # noqa: S101

        # 2. Set an Alert (Alarm for AAPL target $300.00 ABOVE)
        print("\n[2] Setting Price Alarm (POST /portfolio/alerts)...")
        res = await client.post(
            "/portfolio/alerts",
            headers=headers,
            json={"symbol": "AAPL", "target_price": 300.0, "condition": "ABOVE"},
        )
        print(f"    Status: {res.status_code} | Body: {res.json()}")
        assert res.status_code == 201  # noqa: S101
        alert_data = res.json()
        alert_id = alert_data["id"]

        # 3. List active alerts
        print("\n[3] Fetching User Active Alerts (GET /portfolio/alerts)...")
        res = await client.get("/portfolio/alerts", headers=headers)
        print(f"    Status: {res.status_code} | Active Count: {res.json()['total']}")
        assert res.json()["total"] == 1  # noqa: S101
        assert res.json()["items"][0]["is_triggered"] is False  # noqa: S101

        # 4. Simulate Live Market Tick & Evaluate Alarm Ring
        print("\n[4] Simulating Live Price Tick for AAPL at $305.00...")
        alert_service = PriceAlertService()
        async with AsyncSessionFactory() as db:
            triggered = await alert_service.evaluate_price_change(
                db=db,
                symbol="AAPL",
                current_price=305.00,
            )
            print(f"    ALARM RING TRIGGERED! Count: {len(triggered)}")
            assert len(triggered) == 1  # noqa: S101
            print(f"    Triggered Alert ID: {triggered[0].id}")
            print(f"    Triggered Symbol: {triggered[0].symbol}")
            print(f"    Target Price: ${triggered[0].target_price}")
            print(f"    Triggered At: {triggered[0].triggered_at}")

        # 5. Fetch alerts again to confirm is_triggered == True
        print("\n[5] Verifying Alarm Status in Database (GET /portfolio/alerts)...")
        res = await client.get("/portfolio/alerts", headers=headers)
        alert_status = res.json()["items"][0]
        print(f"    is_triggered: {alert_status['is_triggered']}")
        print(f"    triggered_at: {alert_status['triggered_at']}")
        assert alert_status["is_triggered"] is True  # noqa: S101

        # 6. Delete alert
        print(f"\n[6] Deleting Alert (DELETE /portfolio/alerts/{alert_id})...")
        res = await client.delete(f"/portfolio/alerts/{alert_id}", headers=headers)
        print(f"    Status: {res.status_code} (204 No Content)")
        assert res.status_code == 204  # noqa: S101

        print("\n" + "=" * 60)
        print("SUCCESS: ALL ENDPOINTS & LIVE ALARM RING EVALUATION WORK PERFECTLY!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
