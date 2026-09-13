import uuid
from datetime import UTC, datetime

from app.agents.expert_review.schemas import ReviewDecision
from app.api.expert_reviews import (
    REVIEWER_ACCESS_ROLES,
    SubmitHumanReviewRequest,
    serialize_run,
)
from app.database.models import ExpertReviewRun
from app.main import app
from app.services.expert_review_runs import (
    canonical_digest,
    hashes_match,
    review_request_digest,
)


def test_expert_review_routes_are_registered() -> None:
    paths = app.openapi()["paths"]

    assert "/v1/expert-reviews" in paths
    assert "/v1/expert-reviews/{run_id}" in paths
    assert "/v1/expert-reviews/{run_id}/review" in paths


def test_hash_comparison_rejects_invalid_values() -> None:
    digest = "a" * 64

    assert hashes_match(digest, digest) is True
    assert hashes_match(digest, "b" * 64) is False
    assert hashes_match(digest, "short") is False


def test_canonical_digest_is_order_independent() -> None:
    first = canonical_digest(
        {
            "objective": "Increase conversions",
            "metrics": {"clicks": 100, "spend": 200},
        }
    )
    second = canonical_digest(
        {
            "metrics": {"spend": 200, "clicks": 100},
            "objective": "Increase conversions",
        }
    )

    assert first == second


def test_review_request_digest_changes_with_decision() -> None:
    approved = review_request_digest(
        decision=ReviewDecision.APPROVED,
        comments="Reviewed.",
        report_hash="a" * 64,
        reviewer_role="Paid Media Director",
    )
    rejected = review_request_digest(
        decision=ReviewDecision.REJECTED,
        comments="Reviewed.",
        report_hash="a" * 64,
        reviewer_role="Paid Media Director",
    )

    assert approved != rejected


def test_review_request_requires_sha256_hash() -> None:
    request = SubmitHumanReviewRequest(
        decision=ReviewDecision.APPROVED,
        report_hash="a" * 64,
        reviewer_role="Paid Media Director",
        comments="Evidence reviewed.",
    )

    assert request.report_hash == "a" * 64


def test_only_privileged_roles_can_review() -> None:
    assert REVIEWER_ACCESS_ROLES == {"owner", "admin"}


def test_dashboard_response_is_explicit_about_review_state() -> None:
    now = datetime.now(UTC)
    run = ExpertReviewRun(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        status="awaiting_human_review",
        mode="shadow",
        analysis_engine="groq",
        objective="Improve qualified conversions.",
        evidence_data={},
        report_data={"executive_summary": "Review ready."},
        validation_data={"passed": True, "issues": []},
        report_hash="a" * 64,
        rubric_version="advertising-review-v1",
        request_digest="b" * 64,
        created_at=now,
        updated_at=now,
        started_at=now,
    )

    response = serialize_run(run, None)

    assert response.review_required is True
    assert response.mode == "shadow"
    assert response.report_hash == "a" * 64
    assert response.links["review"].endswith("/review")
    assert "human review required" in response.review_label.lower()
