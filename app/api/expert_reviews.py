# ruff: noqa: B008
import uuid
from datetime import datetime
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Response,
)
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.agents.expert_review.schemas import (
    CampaignEvidence,
    ReviewDecision,
)
from app.core.auth import (
    OrganizationContext,
    require_organization_context,
)
from app.database.models import (
    ExpertHumanReview,
    ExpertReviewRun,
)
from app.database.session import get_database_session
from app.services.expert_review_runs import (
    ExpertReviewConflictError,
    ExpertReviewIntegrityError,
    ExpertReviewStateError,
    create_run_record,
    execute_run,
    resume_with_review,
)

router = APIRouter(
    prefix="/v1/expert-reviews",
    tags=["Expert Reviews"],
)

REVIEWER_ACCESS_ROLES = {
    "owner",
    "admin",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateExpertReviewRequest(StrictModel):
    evidence: CampaignEvidence


class SubmitHumanReviewRequest(StrictModel):
    decision: ReviewDecision
    report_hash: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[a-f0-9]{64}$",
    )
    reviewer_role: str = Field(
        min_length=3,
        max_length=200,
    )
    comments: str = Field(
        default="",
        max_length=5000,
    )


class HumanReviewResponse(StrictModel):
    id: uuid.UUID
    decision: ReviewDecision
    reviewer_identity: str
    reviewer_role: str
    comments: str
    report_hash: str
    rubric_version: str
    reviewed_at: datetime


class ExpertReviewRunResponse(StrictModel):
    run_id: uuid.UUID
    status: str
    mode: str
    analysis_engine: str
    objective: str
    report: dict[str, Any] | None
    validation: dict[str, Any] | None
    report_hash: str | None
    rubric_version: str | None
    review_required: bool
    review_label: str
    human_review: HumanReviewResponse | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    links: dict[str, str]
    idempotent: bool = False


def _review_label(
    run: ExpertReviewRun,
    review: ExpertHumanReview | None,
) -> str:
    if review is None:
        if run.status == "awaiting_human_review":
            return "Automated validation passed — human review required"

        if run.status.startswith("failed"):
            return "Automated validation failed"

        return "Expert analysis in progress"

    if review.decision == ReviewDecision.APPROVED.value:
        return "Organization-authorized human review approved"

    if review.decision == ReviewDecision.REVISION_REQUIRED.value:
        return "Human revision required"

    return "Human reviewer rejected"


def serialize_run(
    run: ExpertReviewRun,
    review: ExpertHumanReview | None,
    *,
    idempotent: bool = False,
) -> ExpertReviewRunResponse:
    review_payload = None

    if review is not None:
        review_payload = HumanReviewResponse(
            id=review.id,
            decision=ReviewDecision(review.decision),
            reviewer_identity=review.reviewer_identity,
            reviewer_role=review.reviewer_role,
            comments=review.comments,
            report_hash=review.report_hash,
            rubric_version=review.rubric_version,
            reviewed_at=review.reviewed_at,
        )

    run_url = f"/v1/expert-reviews/{run.id}"

    return ExpertReviewRunResponse(
        run_id=run.id,
        status=run.status,
        mode=run.mode,
        analysis_engine=run.analysis_engine,
        objective=run.objective,
        report=run.report_data,
        validation=run.validation_data,
        report_hash=run.report_hash,
        rubric_version=run.rubric_version,
        review_required=run.status == "awaiting_human_review",
        review_label=_review_label(run, review),
        human_review=review_payload,
        error_message=run.error_message,
        created_at=run.created_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        links={
            "self": run_url,
            "review": f"{run_url}/review",
        },
        idempotent=idempotent,
    )


def load_scoped_run(
    database: Any,
    *,
    run_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> ExpertReviewRun:
    run = database.scalars(
        select(ExpertReviewRun).where(
            ExpertReviewRun.id == run_id,
            ExpertReviewRun.organization_id == organization_id,
        )
    ).one_or_none()

    if run is None:
        raise HTTPException(
            404,
            "Expert-review run was not found.",
        )

    return run


def load_review(
    database: Any,
    run_id: uuid.UUID,
) -> ExpertHumanReview | None:
    return database.scalars(
        select(ExpertHumanReview).where(
            ExpertHumanReview.run_id == run_id,
        )
    ).one_or_none()


@router.post(
    "",
    response_model=ExpertReviewRunResponse,
    status_code=201,
)
def create_expert_review(
    request: CreateExpertReviewRequest,
    response: Response,
    context: OrganizationContext = Depends(require_organization_context),
    database: Any = Depends(get_database_session),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        max_length=255,
    ),
) -> ExpertReviewRunResponse:
    try:
        run, idempotent = create_run_record(
            database,
            context=context,
            evidence=request.evidence,
            idempotency_key=idempotency_key,
        )
    except ExpertReviewConflictError as exc:
        raise HTTPException(409, str(exc)) from exc

    if not idempotent:
        run = execute_run(database, run)

    review = load_review(database, run.id)
    run_url = f"/v1/expert-reviews/{run.id}"
    response.headers["Location"] = run_url

    if idempotent:
        response.status_code = 200

    return serialize_run(
        run,
        review,
        idempotent=idempotent,
    )


@router.get(
    "/{run_id}",
    response_model=ExpertReviewRunResponse,
)
def get_expert_review(
    run_id: uuid.UUID,
    context: OrganizationContext = Depends(require_organization_context),
    database: Any = Depends(get_database_session),
) -> ExpertReviewRunResponse:
    run = load_scoped_run(
        database,
        run_id=run_id,
        organization_id=context.organization_id,
    )
    review = load_review(database, run.id)

    return serialize_run(run, review)


@router.post(
    "/{run_id}/review",
    response_model=ExpertReviewRunResponse,
)
def submit_expert_review(
    run_id: uuid.UUID,
    request: SubmitHumanReviewRequest,
    context: OrganizationContext = Depends(require_organization_context),
    database: Any = Depends(get_database_session),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        max_length=255,
    ),
) -> ExpertReviewRunResponse:
    if context.role not in REVIEWER_ACCESS_ROLES:
        raise HTTPException(
            403,
            "Owner or administrator access is required to submit a human review.",
        )

    run = load_scoped_run(
        database,
        run_id=run_id,
        organization_id=context.organization_id,
    )

    try:
        run, review, idempotent = resume_with_review(
            database,
            run=run,
            context=context,
            decision=request.decision,
            comments=request.comments,
            report_hash=request.report_hash,
            reviewer_role=request.reviewer_role,
            idempotency_key=idempotency_key,
        )
    except ExpertReviewConflictError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ExpertReviewIntegrityError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ExpertReviewStateError as exc:
        raise HTTPException(409, str(exc)) from exc

    return serialize_run(
        run,
        review,
        idempotent=idempotent,
    )
