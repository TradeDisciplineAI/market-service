# Market Service

> **Microservice for real-time market data, quotes, historical OHLCV data, and streaming updates built with FastAPI.**

---

## 🏗️ Architecture

```
src/market_service/
├── core/               ← Foundation: config, database, security, exceptions, dependencies, redis, celery
├── models/             ← SQLAlchemy ORM models (PostgreSQL)
├── schemas/            ← Pydantic request/response validation
├── services/           ← Domain business logic layer
├── workers/            ← Celery worker entrypoints
├── main.py             ← FastAPI application factory
└── __init__.py

alembic/                ← Database migrations
```

## ⚙️ Tech Stack

| Concern | Library |
|---|---|
| Framework | FastAPI (async) |
| Database | PostgreSQL via asyncpg |
| Cache | Redis via redis.asyncio |
| Background Tasks | Celery + Celery Beat |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth Verification | Stateless JWT (PyJWT) |
| Settings | pydantic-settings |
| Package Manager | uv |

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.13+
- Docker & Docker Compose (or local PostgreSQL & Redis)
- [uv](https://docs.astral.sh/uv/) installed

### 2. Setup Development Environment
```powershell
.\scripts\setup.ps1
```

### 3. Configure Environment
```bash
cp .env.example .env
```

### 4. Run Development Server
```bash
uv run uvicorn market_service.main:app --reload
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## 📡 Base Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/` | ❌ | Service status |
| GET | `/health` | ❌ | Health check |

---

## 🧪 Running Tests & Quality Checks
```bash
# Run pytest suite
uv run pytest

# Linting & Type Checking
uv run ruff check .
uv run mypy src
```
# ci test
