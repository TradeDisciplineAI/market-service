"""Locust load test entrypoint for Market Service foundation."""

import logging
from typing import Any

from locust import HttpUser, between, events, task

from tests.performance.config import config
from tests.performance.reporter import generate_native_reports

logger = logging.getLogger(__name__)


@events.test_stop.add_listener
def on_test_stop(environment: Any, **kwargs: Any) -> None:
    """Automatically generate native Locust reports when load test completes."""
    generate_native_reports(environment)


class BackendUser(HttpUser):
    """Locust Virtual User simulating Market Service API queries."""

    host = config.BASE_URL
    wait_time = between(config.MIN_WAIT, config.MAX_WAIT)

    @task(2)
    def task_health_check(self) -> None:
        """Query basic application health baseline (/health)."""
        with self.client.get(
            "/health", catch_response=True, name="/health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Health check failed with status {response.status_code}"
                )

    @task(1)
    def task_root_check(self) -> None:
        """Query root service endpoint (/)."""
        with self.client.get("/", catch_response=True, name="/") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Root endpoint failed with status {response.status_code}"
                )
