import logging
import os
from collections.abc import AsyncGenerator, Generator
from urllib.parse import urlsplit, urlunsplit

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from market_service.core.database import Base

logger = logging.getLogger(__name__)

LOCAL_TEST_DB = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5434/market_test_db",
)
parsed = urlsplit(LOCAL_TEST_DB)
TEST_DATABASE_URL = LOCAL_TEST_DB
admin_url = urlunsplit(parsed._replace(path="/postgres"))


async def create_test_db() -> None:
    """Create the test database if it does not exist."""
    try:
        engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname='market_test_db'")
            )
            if not result.scalar():
                await conn.execute(text("CREATE DATABASE market_test_db"))
        await engine.dispose()
    except Exception as exc:
        # PostgreSQL host may not be running during standalone unit test runs
        logger.debug("PostgreSQL host connection skipped during test setup: %s", exc)


@pytest.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine]:
    """Create a database engine scoped to the test's event loop."""
    await create_test_db()

    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"statement_cache_size": 0},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(table.delete())
        except Exception as exc:
            logger.debug("Table truncation skipped: %s", exc)

    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(
    db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Yield a session factory bound to the test engine."""
    return async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    """Yield a database session from the test session factory."""
    async with session_factory() as session:
        yield session


@pytest.fixture(autouse=True)
def patch_session_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> Generator[None]:
    """Patch global AsyncSessionFactory to use test session factory during tests."""
    from market_service.core import database

    old_factory = database.AsyncSessionFactory
    database.AsyncSessionFactory = session_factory
    yield
    database.AsyncSessionFactory = old_factory
