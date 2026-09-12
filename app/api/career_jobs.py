# ruff: noqa: B008
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from app.core.auth import (
    OrganizationContext,
    require_organization_context,
)
from app.database.models.jobs import (
    CanonicalJob,
    JobSourcePosting,
)
from app.database.session import SessionLocal

router = APIRouter(
    prefix="/v1/career/jobs",
    tags=["Career canonical jobs"],
)


def serialize_job(
    job: CanonicalJob,
    source_count: int,
) -> dict[str, Any]:
    return {
        "id": str(job.id),
        "employer_name": job.employer_name,
        "employer_domain": job.employer_domain,
        "title": job.title,
        "normalized_title": job.normalized_title,
        "location": job.location_text,
        "team": job.team,
        "employment_type": job.employment_type,
        "canonical_apply_url": job.canonical_apply_url,
        "status": job.status,
        "description_hash": job.description_hash,
        "source_count": source_count,
        "first_seen_at": job.first_seen_at.isoformat(),
        "last_seen_at": job.last_seen_at.isoformat(),
    }


@router.get("")
def list_canonical_jobs(
    status: str = Query(default="active"),
    query: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=100, ge=1, le=500),
    context: OrganizationContext = Depends(require_organization_context),
) -> list[dict[str, Any]]:
    del context

    source_count = (
        select(
            JobSourcePosting.canonical_job_id,
            func.count(JobSourcePosting.id).label("source_count"),
        )
        .where(JobSourcePosting.is_active.is_(True))
        .group_by(JobSourcePosting.canonical_job_id)
        .subquery()
    )

    statement = (
        select(
            CanonicalJob,
            func.coalesce(
                source_count.c.source_count,
                0,
            ),
        )
        .outerjoin(
            source_count,
            source_count.c.canonical_job_id == CanonicalJob.id,
        )
        .where(CanonicalJob.status == status)
    )

    if query and query.strip():
        pattern = f"%{query.strip()}%"
        statement = statement.where(
            CanonicalJob.title.ilike(pattern)
            | CanonicalJob.employer_name.ilike(pattern)
        )

    statement = statement.order_by(CanonicalJob.last_seen_at.desc()).limit(limit)

    with SessionLocal() as database:
        return [
            serialize_job(job, int(count))
            for job, count in database.execute(statement).all()
        ]


@router.get("/{job_id}")
def canonical_job_detail(
    job_id: uuid.UUID,
    context: OrganizationContext = Depends(require_organization_context),
) -> dict[str, Any]:
    del context

    with SessionLocal() as database:
        job = database.get(CanonicalJob, job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Canonical job was not found.",
            )

        sources = database.scalars(
            select(JobSourcePosting)
            .where(JobSourcePosting.canonical_job_id == job.id)
            .order_by(
                JobSourcePosting.is_active.desc(),
                JobSourcePosting.last_seen_at.desc(),
            )
        ).all()

        result = serialize_job(
            job,
            sum(1 for source in sources if source.is_active),
        )
        result["description_text"] = job.description_text
        result["sources"] = [
            {
                "id": str(source.id),
                "provider": source.provider,
                "external_id": source.external_id,
                "adapter_version": source.adapter_version,
                "source_url": source.source_url,
                "apply_url": source.apply_url,
                "active": source.is_active,
                "last_seen_at": source.last_seen_at.isoformat(),
            }
            for source in sources
        ]
        return result
