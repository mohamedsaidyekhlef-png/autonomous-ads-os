import hashlib
import json

from app.agents.expert_review.evidence import (
    calculate_campaign_metrics,
)
from app.agents.expert_review.schemas import (
    CampaignEvidence,
    ExpertAnalysisReport,
    HumanReview,
    Provenance,
    ReviewDecision,
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
)


def report_digest(report: ExpertAnalysisReport) -> str:
    payload = report.model_dump(
        mode="json",
        exclude={"automated_validation_passed"},
    )
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_expert_report(
    report: ExpertAnalysisReport,
    evidence: CampaignEvidence,
) -> ValidationResult:
    issues: list[ValidationIssue] = []

    known_evidence_ids = {item.id for item in evidence.evidence}
    known_evidence_ids.update(datum.evidence_id for datum in evidence.metrics.values())

    calculated_metrics = calculate_campaign_metrics(evidence)

    for metric in calculated_metrics:
        if metric.available:
            known_evidence_ids.add(f"calculated:{metric.name.value}")

    if report.mode != "shadow":
        issues.append(
            ValidationIssue(
                code="invalid_mode",
                level=ValidationLevel.ERROR,
                message=("Expert analysis must remain in Shadow Mode."),
                path="mode",
            )
        )

    if report.execution_requested:
        issues.append(
            ValidationIssue(
                code="execution_requested",
                level=ValidationLevel.ERROR,
                message=(
                    "An analysis report cannot request or perform "
                    "a live advertising mutation."
                ),
                path="execution_requested",
            )
        )

    if not report.specialist_assessments:
        issues.append(
            ValidationIssue(
                code="missing_specialists",
                level=ValidationLevel.ERROR,
                message=("At least one specialist assessment is required."),
                path="specialist_assessments",
            )
        )

    findings = [
        finding
        for assessment in report.specialist_assessments
        for finding in assessment.findings
    ]

    recommendations = [
        recommendation
        for assessment in report.specialist_assessments
        for recommendation in assessment.recommendations
    ] + report.prioritized_recommendations

    for index, finding in enumerate(findings):
        path = f"findings.{index}"

        if (
            finding.basis in {Provenance.ACTUAL, Provenance.CALCULATED}
            and not finding.evidence_ids
        ):
            issues.append(
                ValidationIssue(
                    code="missing_finding_evidence",
                    level=ValidationLevel.ERROR,
                    message=(
                        "Actual and calculated findings require evidence references."
                    ),
                    path=f"{path}.evidence_ids",
                )
            )

        for evidence_id in finding.evidence_ids:
            if evidence_id not in known_evidence_ids:
                issues.append(
                    ValidationIssue(
                        code="unknown_evidence_reference",
                        level=ValidationLevel.ERROR,
                        message=(f"Unknown evidence reference {evidence_id!r}."),
                        path=f"{path}.evidence_ids",
                    )
                )

        if finding.basis == Provenance.AI_ESTIMATE and finding.confidence > 0.85:
            issues.append(
                ValidationIssue(
                    code="high_estimate_confidence",
                    level=ValidationLevel.WARNING,
                    message=(
                        "AI-estimated findings above 85% "
                        "confidence require human scrutiny."
                    ),
                    path=f"{path}.confidence",
                )
            )

    for index, recommendation in enumerate(recommendations):
        path = f"recommendations.{index}"

        if not recommendation.evidence_ids:
            issues.append(
                ValidationIssue(
                    code="unsupported_recommendation",
                    level=ValidationLevel.ERROR,
                    message=(
                        "Every recommendation requires at least one evidence reference."
                    ),
                    path=f"{path}.evidence_ids",
                )
            )

        for evidence_id in recommendation.evidence_ids:
            if evidence_id not in known_evidence_ids:
                issues.append(
                    ValidationIssue(
                        code="unknown_evidence_reference",
                        level=ValidationLevel.ERROR,
                        message=(f"Unknown evidence reference {evidence_id!r}."),
                        path=f"{path}.evidence_ids",
                    )
                )

        if not recommendation.requires_human_approval:
            issues.append(
                ValidationIssue(
                    code="human_approval_disabled",
                    level=ValidationLevel.ERROR,
                    message=(
                        "Recommendations must require human "
                        "approval during Shadow Mode."
                    ),
                    path=f"{path}.requires_human_approval",
                )
            )

    errors = [issue for issue in issues if issue.level == ValidationLevel.ERROR]

    return ValidationResult(
        passed=not errors,
        issues=issues,
    )


def review_label(
    report: ExpertAnalysisReport,
    review: HumanReview | None,
) -> str:
    if review is None:
        return "Expert framework applied ? human review required"

    if review.report_hash != report_digest(report):
        return "Expert framework applied ? human review invalidated"

    if review.rubric_version != report.rubric_version:
        return "Expert framework applied ? rubric mismatch"

    if review.decision == ReviewDecision.APPROVED:
        return "Human expert vetted"

    if review.decision == ReviewDecision.REVISION_REQUIRED:
        return "Human expert revision required"

    return "Human expert rejected"
