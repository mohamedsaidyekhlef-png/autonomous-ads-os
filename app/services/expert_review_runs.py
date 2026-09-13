import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from langgraph.types import Command
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.expert_review.checkpointing import (
    expert_review_checkpointer,
)
from app.agents.expert_review.graph import (
    build_expert_review_graph,
    build_live_expert_review_graph,
)
from app.agents.expert_review.schemas import (
    CampaignEvidence,
    ExpertAnalysisReport,
    ReviewDecision,
)
from app.agents.expert_review.validators import report_digest
from app.core.auth import OrganizationContext
from app.core.settings import get_settings
from app.database.models import (
    ExpertHumanReview,
    ExpertReviewRun,
)


class ExpertReviewConflictError(RuntimeError):
    pass


class ExpertReviewIntegrityError(RuntimeError):
    pass


class ExpertReviewStateError(RuntimeError):
    pass


def canonical_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def hashes_match(expected: str, submitted: str) -> bool:
    if len(expected) != 64 or len(submitted) != 64:
        return False

    return hmac.compare_digest(expected, submitted)


def graph_config(run: ExpertReviewRun) -> dict[str, Any]:
    return {
        "configurable": {"thread_id": (f"expert-review:{run.organization_id}:{run.id}")}
    }


def reviewer_identity(context: OrganizationContext) -> str:
    if context.user_id is not None:
        return str(context.user_id)

    return "development-reviewer"


def _build_graph(checkpointer: Any):
    settings = get_settings()

    if getattr(settings, "groq_api_key", None):
        return (
            build_live_expert_review_graph(
                checkpointer=checkpointer,
            ),
            "groq",
        )

    return (
        build_expert_review_graph(
            checkpointer=checkpointer,
        ),
        "deterministic",
    )


def find_existing_run(
    database: Session,
    *,
    organization_id: uuid.UUID,
    idempotency_key: str | None,
) -> ExpertReviewRun | None:
    if not idempotency_key:
        return None

    return database.scalars(
        select(ExpertReviewRun).where(
            ExpertReviewRun.organization_id == organization_id,
            ExpertReviewRun.idempotency_key == idempotency_key,
        )
    ).one_or_none()


def create_run_record(
    database: Session,
    *,
    context: OrganizationContext,
    evidence: CampaignEvidence,
    idempotency_key: str | None,
) -> tuple[ExpertReviewRun, bool]:
    evidence_payload = evidence.model_dump(mode="json")
    request_digest = canonical_digest(evidence_payload)

    existing = find_existing_run(
        database,
        organization_id=context.organization_id,
        idempotency_key=idempotency_key,
    )

    if existing is not None:
        if existing.request_digest != request_digest:
            raise ExpertReviewConflictError(
                "The idempotency key was already used with different evidence."
            )

        return existing, True

    run = ExpertReviewRun(
        organization_id=context.organization_id,
        created_by_user_id=context.user_id,
        status="queued",
        mode="shadow",
        analysis_engine="pending",
        objective=evidence.objective,
        evidence_data=evidence_payload,
        request_digest=request_digest,
        idempotency_key=idempotency_key,
    )

    database.add(run)
    database.commit()
    database.refresh(run)

    return run, False


def execute_run(
    database: Session,
    run: ExpertReviewRun,
) -> ExpertReviewRun:
    if run.status not in {"queued", "failed"}:
        return run

    evidence = CampaignEvidence.model_validate(run.evidence_data)

    run.status = "running"
    run.started_at = datetime.now(UTC)
    run.completed_at = None
    run.error_message = None
    database.commit()

    try:
        with expert_review_checkpointer() as checkpointer:
            graph, engine = _build_graph(checkpointer)
            run.analysis_engine = engine
            database.commit()

            result = graph.invoke(
                {
                    "run_id": str(run.id),
                    "evidence": evidence,
                    "specialist_assessments": [],
                    "status": "queued",
                },
                config=graph_config(run),
            )

        report = result.get("draft_report")
        validation = result.get("validation")

        run.status = str(result.get("status", "failed"))
        run.report_data = report.model_dump(mode="json") if report is not None else None
        run.validation_data = (
            validation.model_dump(mode="json") if validation is not None else None
        )
        run.report_hash = report_digest(report) if report is not None else None
        run.rubric_version = report.rubric_version if report is not None else None

        if run.status != "awaiting_human_review":
            run.completed_at = datetime.now(UTC)

        database.commit()
        database.refresh(run)

        return run
    # This is the run-level failure boundary: provider, graph, and
    # checkpoint errors must all be persisted as a failed run.
    except Exception as exc:  # noqa: BLE001
        run.status = "failed"
        run.error_message = f"Expert analysis could not be completed: {str(exc)[:1000]}"
        run.completed_at = datetime.now(UTC)
        database.commit()
        database.refresh(run)

        return run


def validate_stored_report(
    run: ExpertReviewRun,
    submitted_hash: str,
) -> ExpertAnalysisReport:
    if run.report_data is None or run.report_hash is None:
        raise ExpertReviewStateError(
            "The run has no validated report available for review."
        )

    report = ExpertAnalysisReport.model_validate(run.report_data)
    calculated_hash = report_digest(report)

    if not hashes_match(run.report_hash, calculated_hash):
        raise ExpertReviewIntegrityError(
            "The stored report failed integrity verification."
        )

    if not hashes_match(calculated_hash, submitted_hash):
        raise ExpertReviewConflictError(
            "The submitted report hash does not match the current report."
        )

    return report


def review_request_digest(
    *,
    decision: ReviewDecision,
    comments: str,
    report_hash: str,
    reviewer_role: str,
) -> str:
    return canonical_digest(
        {
            "decision": decision.value,
            "comments": comments,
            "report_hash": report_hash,
            "reviewer_role": reviewer_role,
        }
    )


def find_existing_review(
    database: Session,
    run_id: uuid.UUID,
) -> ExpertHumanReview | None:
    return database.scalars(
        select(ExpertHumanReview).where(
            ExpertHumanReview.run_id == run_id,
        )
    ).one_or_none()


def resume_with_review(
    database: Session,
    *,
    run: ExpertReviewRun,
    context: OrganizationContext,
    decision: ReviewDecision,
    comments: str,
    report_hash: str,
    reviewer_role: str,
    idempotency_key: str | None,
) -> tuple[ExpertReviewRun, ExpertHumanReview, bool]:
    digest = review_request_digest(
        decision=decision,
        comments=comments,
        report_hash=report_hash,
        reviewer_role=reviewer_role,
    )

    existing_review = find_existing_review(database, run.id)

    if existing_review is not None:
        if existing_review.request_digest != digest:
            raise ExpertReviewConflictError(
                "A different human-review decision "
                "has already been recorded for this run."
            )

        return run, existing_review, True

    if run.status != "awaiting_human_review":
        raise ExpertReviewStateError("Only runs awaiting human review can be reviewed.")

    report = validate_stored_report(run, report_hash)
    identity = reviewer_identity(context)

    run.status = "review_processing"
    run.error_message = None
    database.commit()

    try:
        with expert_review_checkpointer() as checkpointer:
            graph, _ = _build_graph(checkpointer)

            result = graph.invoke(
                Command(
                    resume={
                        "decision": decision.value,
                        "reviewer_id": identity,
                        "reviewer_role": reviewer_role,
                        "comments": comments,
                    }
                ),
                config=graph_config(run),
            )

        final_status = str(result.get("status", ""))

        if final_status not in {
            "completed",
            "rejected",
            "revision_required",
        }:
            raise RuntimeError(
                "The expert-review graph returned "
                f"an invalid final status: {final_status!r}."
            )

        graph_review = result.get("human_review")

        if graph_review is None:
            raise RuntimeError("The graph did not produce a human-review record.")

        if not hashes_match(
            graph_review.report_hash,
            report_digest(report),
        ):
            raise ExpertReviewIntegrityError(
                "The graph review references a different report."
            )

        review = ExpertHumanReview(
            run_id=run.id,
            organization_id=run.organization_id,
            reviewer_user_id=context.user_id,
            reviewer_identity=identity,
            reviewer_role=reviewer_role,
            decision=decision.value,
            comments=comments,
            report_hash=graph_review.report_hash,
            rubric_version=report.rubric_version,
            idempotency_key=idempotency_key,
            request_digest=digest,
            reviewed_at=graph_review.reviewed_at,
        )

        database.add(review)

        run.status = final_status
        run.completed_at = datetime.now(UTC)
        run.error_message = None

        database.commit()
        database.refresh(run)
        database.refresh(review)

        return run, review, False
    except Exception:
        database.rollback()

        refreshed = database.get(ExpertReviewRun, run.id)

        if refreshed is not None:
            refreshed.status = "awaiting_human_review"
            refreshed.error_message = (
                "Human-review processing failed before completion."
            )
            database.commit()

        raise
