"""Celery worker entrypoint module for market-service background processing."""

from market_service.core.celery import celery_app

__all__ = ["celery_app"]
