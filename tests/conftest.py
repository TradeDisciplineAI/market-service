import os

from market_service.core.config import get_settings

# Configure test-only allowed hosts and local database before importing the FastAPI application.
os.environ["ALLOWED_HOSTS"] = '["localhost", "127.0.0.1", "testserver"]'
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5434/market_test_db"
get_settings.cache_clear()

pytest_plugins = [
    "tests.fixtures.database",
    "tests.fixtures.client",
]
