"""Application entry point."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .core.config import get_settings
from .core.exceptions import AppException
from .core.limiter import limiter
from .routers.alerts import router as alerts_router
from .routers.dashboard import router as dashboard_router
from .routers.portfolio import router as portfolio_router
from .routers.internal import router as internal_router

settings = get_settings()


# Initialize logging configuration
logging.basicConfig(
    level=settings.log_level,
    format=settings.log_format,
)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Market Service microservice.",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
)

# Instrument FastAPI HTTP metrics and expose GET /metrics endpoint
Instrumentator().instrument(app).expose(app)

# Attach limiter state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Market Service is running."}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.app_version, "env": settings.app_env}


@app.get("/health/celery-ping")
async def celery_ping() -> dict[str, str]:
    from market_service.tasks.system_tasks import ping_market_worker

    task = ping_market_worker.delay()
    return {"status": "enqueued", "task_id": task.id, "queue": "market_queue"}


app.include_router(dashboard_router)
app.include_router(portfolio_router)
app.include_router(alerts_router)
app.include_router(internal_router)
