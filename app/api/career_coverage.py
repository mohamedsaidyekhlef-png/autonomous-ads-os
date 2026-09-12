# ruff: noqa: B008
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.auth import OrganizationContext, require_organization_context
from app.database.models.career import ATSBoard, ATSDriftAlert
from app.database.session import SessionLocal

router = APIRouter(
    prefix="/v1/career/coverage",
    tags=["Career ATS coverage"],
)

SUPPORTED_PROVIDERS = {
    "ashby",
    "bamboohr",
    "greenhouse",
    "lever",
    "personio",
    "recruitee",
    "smartrecruiters",
    "teamtailor",
    "workable",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BoardCreate(StrictModel):
    employer_name: str = Field(min_length=2, max_length=255)
    employer_domain: str = Field(min_length=3, max_length=255)
    provider: str = Field(min_length=2, max_length=50)
    board_token: str = Field(min_length=1, max_length=500)
    board_url: AnyHttpUrl
    careers_url: AnyHttpUrl | None = None
    source_method: str = Field(default="manual", max_length=30)


def aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def serialize_board(board: ATSBoard) -> dict[str, Any]:
    return {
        "id": str(board.id),
        "employer_name": board.employer_name,
        "employer_domain": board.employer_domain,
        "provider": board.provider,
        "board_token": board.board_token,
        "board_url": board.board_url,
        "careers_url": board.careers_url,
        "source_method": board.source_method,
        "state": board.state,
        "posting_count": board.posting_count,
        "schema_hash": board.schema_hash,
        "consecutive_failures": board.consecutive_failures,
        "last_checked_at": (
            board.last_checked_at.isoformat() if board.last_checked_at else None
        ),
        "last_successful_fetch_at": (
            board.last_successful_fetch_at.isoformat()
            if board.last_successful_fetch_at
            else None
        ),
        "next_check_at": (
            board.next_check_at.isoformat() if board.next_check_at else None
        ),
    }


@router.get("/summary")
def coverage_summary(
    context: OrganizationContext = Depends(require_organization_context),
) -> dict[str, Any]:
    del context

    with SessionLocal() as database:
        state_rows = database.execute(
            select(ATSBoard.state, func.count(ATSBoard.id)).group_by(ATSBoard.state)
        ).all()

        provider_rows = database.execute(
            select(ATSBoard.provider, func.count(ATSBoard.id))
            .group_by(ATSBoard.provider)
            .order_by(func.count(ATSBoard.id).desc())
        ).all()

        live_fetches = database.scalars(
            select(ATSBoard.last_successful_fetch_at).where(
                ATSBoard.state == "live",
                ATSBoard.last_successful_fetch_at.is_not(None),
            )
        ).all()

        now = datetime.now(UTC)
        freshness_hours = sorted(
            max(0.0, (now - aware(value)).total_seconds() / 3600)
            for value in live_fetches
            if value is not None
        )

        median_freshness = None

        if freshness_hours:
            middle = len(freshness_hours) // 2

            if len(freshness_hours) % 2:
                median_freshness = freshness_hours[middle]
            else:
                median_freshness = (
                    freshness_hours[middle - 1] + freshness_hours[middle]
                ) / 2

        open_alerts = (
            database.scalar(
                select(func.count(ATSDriftAlert.id)).where(
                    ATSDriftAlert.status == "open"
                )
            )
            or 0
        )

        states = {state: count for state, count in state_rows}

        return {
            "target_live_boards": 5000,
            "actual": {
                "total": sum(states.values()),
                "discovered": states.get("discovered", 0),
                "validated": states.get("validated", 0),
                "live": states.get("live", 0),
                "degraded": states.get("degraded", 0),
                "dead": states.get("dead", 0),
            },
            "median_live_freshness_hours": median_freshness,
            "freshness_target_hours": 6,
            "open_drift_alerts": open_alerts,
            "providers": [
                {"provider": provider, "boards": count}
                for provider, count in provider_rows
            ],
            "data_provenance": "database",
        }


@router.get("/boards")
def list_boards(
    state: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    context: OrganizationContext = Depends(require_organization_context),
) -> list[dict[str, Any]]:
    del context

    query = select(ATSBoard)

    if state:
        query = query.where(ATSBoard.state == state.lower())

    if provider:
        query = query.where(ATSBoard.provider == provider.lower())

    query = query.order_by(
        ATSBoard.updated_at.desc(),
        ATSBoard.employer_name,
    ).limit(limit)

    with SessionLocal() as database:
        return [serialize_board(board) for board in database.scalars(query).all()]


@router.post("/boards", status_code=201)
def register_board(
    payload: BoardCreate,
    context: OrganizationContext = Depends(require_organization_context),
) -> dict[str, Any]:
    provider = payload.provider.strip().lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=422,
            detail=(
                "Unsupported ATS provider. Use one of: "
                + ", ".join(sorted(SUPPORTED_PROVIDERS))
            ),
        )

    employer_domain = payload.employer_domain.strip().lower()
    employer_domain = employer_domain.removeprefix("www.")

    board = ATSBoard(
        discovered_by_organization_id=context.organization_id,
        employer_name=payload.employer_name.strip(),
        employer_domain=employer_domain,
        provider=provider,
        board_token=payload.board_token.strip(),
        board_url=str(payload.board_url),
        careers_url=(str(payload.careers_url) if payload.careers_url else None),
        source_method=payload.source_method.strip().lower(),
        state="discovered",
        posting_count=0,
        consecutive_failures=0,
        board_metadata={
            "registered_by_role": context.role,
        },
    )

    with SessionLocal() as database:
        database.add(board)

        try:
            database.commit()
        except IntegrityError as exc:
            database.rollback()
            raise HTTPException(
                status_code=409,
                detail="This ATS board is already registered.",
            ) from exc

        database.refresh(board)
        return serialize_board(board)


@router.get("/drift-alerts")
def list_drift_alerts(
    status: str = Query(default="open"),
    limit: int = Query(default=100, ge=1, le=500),
    context: OrganizationContext = Depends(require_organization_context),
) -> list[dict[str, Any]]:
    del context

    query = (
        select(ATSDriftAlert, ATSBoard)
        .join(ATSBoard, ATSBoard.id == ATSDriftAlert.board_id)
        .where(ATSDriftAlert.status == status)
        .order_by(ATSDriftAlert.detected_at.desc())
        .limit(limit)
    )

    with SessionLocal() as database:
        return [
            {
                "id": str(alert.id),
                "board_id": str(board.id),
                "employer_name": board.employer_name,
                "provider": board.provider,
                "board_url": board.board_url,
                "status": alert.status,
                "detected_at": alert.detected_at.isoformat(),
                "previous_schema_hash": alert.previous_schema_hash,
                "observed_schema_hash": alert.observed_schema_hash,
                "details": alert.details,
            }
            for alert, board in database.execute(query).all()
        ]
