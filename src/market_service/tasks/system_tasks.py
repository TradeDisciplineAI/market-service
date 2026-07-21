import logging

from market_service.core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="market_service.tasks.ping_market_worker")
def ping_market_worker() -> dict[str, str]:
    """Infrastructure verification ping task for market-service worker."""
    logger.info("Executing market worker infrastructure ping task")
    return {"status": "pong", "service": "market-service"}
