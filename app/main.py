from datetime import UTC, datetime

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.automation import router as automation_router
from app.api.command_center import router as command_center_router
from app.api.oauth import router as oauth_router
from app.api.organization import router as organization_router
from app.api.whop import router as whop_router
from app.core.settings import get_settings
from app.database.session import SessionLocal

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Autonomous multi-platform advertising operating system",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "documentation": "/docs",
    }


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "healthy",
        "application": settings.app_name,
        "environment": settings.app_env,
        "dry_run": settings.dry_run,
        "model": settings.ollama_model,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/ready")
def readiness() -> JSONResponse:
    checks: dict[str, dict[str, object]] = {}

    try:
        with SessionLocal() as session:
            value = session.execute(text("SELECT 1")).scalar_one()

        checks["database"] = {
            "status": "healthy",
            "value": value,
        }
    except SQLAlchemyError as exc:
        checks["database"] = {
            "status": "unhealthy",
            "error": type(exc).__name__,
        }

    try:
        redis_client = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        redis_response = redis_client.ping()

        checks["redis"] = {
            "status": "healthy" if redis_response else "unhealthy",
        }
    except RedisError as exc:
        checks["redis"] = {
            "status": "unhealthy",
            "error": type(exc).__name__,
        }

    try:
        response = httpx.get(
            f"{settings.ollama_base_url.rstrip('/')}/api/tags",
            timeout=5,
        )
        response.raise_for_status()

        available_models = [
            model.get("name") for model in response.json().get("models", [])
        ]

        checks["ollama"] = {
            "status": "healthy",
            "selected_model": settings.ollama_model,
            "model_available": settings.ollama_model in available_models,
        }
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        checks["ollama"] = {
            "status": "unhealthy",
            "error": type(exc).__name__,
        }

    is_ready = all(check["status"] == "healthy" for check in checks.values())

    payload = {
        "status": "ready" if is_ready else "not_ready",
        "dry_run": settings.dry_run,
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    return JSONResponse(
        status_code=200 if is_ready else 503,
        content=payload,
    )


app.include_router(automation_router)

app.include_router(oauth_router)

app.include_router(command_center_router)
app.include_router(organization_router)
app.include_router(whop_router)
