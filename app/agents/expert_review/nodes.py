from typing import Any

from langgraph.types import interrupt

from app.agents.expert_review.evidence import (
    calculate_campaign_metrics,
    validate_campaign_evidence,
)
from app.agents.expert_review.schemas import (
    ExpertAnalysisReport,
    HumanReview,
    ReviewDecision,
)
from app.agents.expert_review.state import ExpertReviewState
from app.agents.expert_review.validators import (
    report_digest,
    validate_expert_report,
)


def validate_evidence_node(
    state: ExpertReviewState,
) -> dict[str, Any]:
    validation = validate_campaign_evidence(state["evidence"])

    return {
        "validation": validation,
        "status": (
            "evidence_validated" if validation.passed else "failed_evidence_validation"
        ),
    }


def calculate_metrics_node(
    state: ExpertReviewState,
) -> dict[str, Any]:
    return {
        "calculated_metrics": calculate_campaign_metrics(state["evidence"]),
        "status": "metrics_calculated",
    }


def synthesize_report_node(
    state: ExpertReviewState,
) -> dict[str, Any]:
    assessments = state.get(
        "specialist_assessments",
        [],
    )

    recommendations = [
        recommendation
        for assessment in assessments
        for recommendation in assessment.recommendations
    ]

    missing_information = sorted(
        {item for assessment in assessments for item in assessment.missing_information}
    )

    contradictions = sorted(
        {item for assessment in assessments for item in assessment.conflicts}
    )

    evidence_validation = validate_campaign_evidence(state["evidence"])

    penalty = min(
        0.8,
        len(evidence_validation.issues) * 0.1,
    )
    quality_score = max(0.0, 1.0 - penalty)

    report = ExpertAnalysisReport(
        run_id=state["run_id"],
        rubric_version="advertising-review-v1",
        mode="shadow",
        executive_summary=(
            "Four governed advertising specialists reviewed the "
            "supplied evidence. Recommendations remain proposals "
            "until automated validation and human review complete."
        ),
        data_quality_score=quality_score,
        specialist_assessments=assessments,
        prioritized_recommendations=recommendations,
        assumptions=state["evidence"].assumptions,
        missing_information=missing_information,
        contradictions=contradictions,
        execution_requested=False,
        automated_validation_passed=False,
    )

    return {
        "draft_report": report,
        "status": "report_synthesized",
    }


def validate_report_node(
    state: ExpertReviewState,
) -> dict[str, Any]:
    report = state["draft_report"]
    validation = validate_expert_report(
        report,
        state["evidence"],
    )

    validated_report = report.model_copy(
        update={
            "automated_validation_passed": validation.passed,
        }
    )

    return {
        "draft_report": validated_report,
        "validation": validation,
        "status": (
            "awaiting_human_review" if validation.passed else "failed_report_validation"
        ),
    }


def human_review_node(
    state: ExpertReviewState,
) -> dict[str, Any]:
    report = state["draft_report"]
    digest = report_digest(report)

    response = interrupt(
        {
            "type": "human_expert_review",
            "run_id": state["run_id"],
            "report_hash": digest,
            "rubric_version": report.rubric_version,
            "allowed_decisions": [
                ReviewDecision.APPROVED.value,
                ReviewDecision.REJECTED.value,
                ReviewDecision.REVISION_REQUIRED.value,
            ],
            "message": (
                "A qualified human reviewer must review the "
                "evidence and recommendations."
            ),
        }
    )

    if not isinstance(response, dict):
        raise TypeError("Human review response must be an object.")

    decision = ReviewDecision(str(response.get("decision", "")))
    reviewer_id = str(response.get("reviewer_id", "")).strip()
    reviewer_role = str(response.get("reviewer_role", "")).strip()
    comments = str(response.get("comments", "")).strip()

    review = HumanReview(
        report_hash=digest,
        reviewer_id=reviewer_id,
        reviewer_role=reviewer_role,
        decision=decision,
        comments=comments,
        rubric_version=report.rubric_version,
    )

    return {
        "human_review": review,
        "status": "human_review_recorded",
    }


def finalize_node(
    state: ExpertReviewState,
) -> dict[str, Any]:
    decision = state["human_review"].decision

    if decision == ReviewDecision.APPROVED:
        status = "completed"
    elif decision == ReviewDecision.REVISION_REQUIRED:
        status = "revision_required"
    else:
        status = "rejected"

    return {"status": status}
