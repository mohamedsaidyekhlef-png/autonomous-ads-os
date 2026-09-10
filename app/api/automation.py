from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.settings import get_settings
from app.database.session import engine

router = APIRouter(prefix="/v1/automation", tags=["automation"])


class StartAutomationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["shadow"] = "shadow"


@router.post("/start")
def start_automation(request: StartAutomationRequest) -> JSONResponse:
    settings = get_settings()

    try:
        with engine.connect() as connection:
            connected_accounts = connection.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM platform_connections
                    WHERE LOWER(status) = 'connected'
                    """
                )
            ).scalar_one()
    except SQLAlchemyError as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "failed",
                "message": "The database readiness check failed.",
                "error_type": type(exc).__name__,
            },
        )

    if connected_accounts == 0:
        return JSONResponse(
            status_code=409,
            content={
                "status": "setup_required",
                "reason": "no_connected_ad_accounts",
                "message": (
                    "Connect at least one Google Ads, Meta Ads, or TikTok Ads "
                    "account before starting the AI Ads Team."
                ),
                "next_step": "/connections",
            },
        )

    run_id = str(uuid4())

    return JSONResponse(
        status_code=202,
        content={
            "status": "readiness_verified",
            "run_id": run_id,
            "mode": request.mode,
            "connected_accounts": connected_accounts,
            "dry_run": settings.dry_run,
            "message": (
                "Account readiness passed. The system is ready for the "
                "agent-workflow milestone."
            ),
            "started_at": datetime.now(UTC).isoformat(),
        },
    )
