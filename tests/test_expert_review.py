from datetime import UTC, datetime
from decimal import Decimal

from app.agents.expert_review.evidence import (
    calculate_campaign_metrics,
    validate_campaign_evidence,
)
from app.agents.expert_review.schemas import (
    CampaignEvidence,
    ExpertAnalysisReport,
    Finding,
    HumanReview,
    MetricDatum,
    MetricName,
    Provenance,
    Recommendation,
    ReviewDecision,
    Severity,
    SpecialistAssessment,
)
from app.agents.expert_review.validators import (
    report_digest,
    review_label,
    validate_expert_report,
)


def metric(
    value: str,
    evidence_id: str,
) -> MetricDatum:
    return MetricDatum(
        value=Decimal(value),
        provenance=Provenance.ACTUAL,
        evidence_id=evidence_id,
        source="uploaded_campaign_csv",
    )


def valid_evidence() -> CampaignEvidence:
    return CampaignEvidence(
        objective="Generate qualified B2B software leads.",
        currency="usd",
        metrics={
            MetricName.IMPRESSIONS: metric(
                "1000",
                "metric-impressions",
            ),
            MetricName.CLICKS: metric(
                "100",
                "metric-clicks",
            ),
            MetricName.SPEND: metric(
                "500",
                "metric-spend",
            ),
            MetricName.CONVERSIONS: metric(
                "10",
                "metric-conversions",
            ),
            MetricName.REVENUE: metric(
                "2000",
                "metric-revenue",
            ),
        },
    )


def recommendation() -> Recommendation:
    return Recommendation(
        title="Review high-cost search terms",
        rationale=(
            "Uploaded spend and conversion evidence supports "
            "a search-term efficiency review."
        ),
        expected_impact=(
            "Potential reduction in irrelevant spend; impact remains an estimate."
        ),
        measurement_plan=(
            "Compare qualified CPA and conversion volume "
            "before and after an approved test."
        ),
        risk=Severity.LOW,
        confidence=0.8,
        evidence_ids=[
            "metric-spend",
            "metric-conversions",
        ],
        reversible=True,
        requires_human_approval=True,
    )


def valid_report() -> ExpertAnalysisReport:
    item = recommendation()

    return ExpertAnalysisReport(
        run_id="run-12345678",
        rubric_version="ads-review-v1",
        executive_summary=(
            "Uploaded evidence supports a controlled search-term efficiency review."
        ),
        data_quality_score=0.8,
        specialist_assessments=[
            SpecialistAssessment(
                agent_id="measurement_auditor",
                role_name="Measurement Auditor",
                findings=[
                    Finding(
                        title="Current cost per acquisition",
                        observation=(
                            "CPA is calculated from uploaded "
                            "spend and conversion totals."
                        ),
                        significance=("CPA should be monitored before budget changes."),
                        severity=Severity.INFO,
                        basis=Provenance.CALCULATED,
                        evidence_ids=[
                            "metric-spend",
                            "metric-conversions",
                        ],
                        confidence=1.0,
                        limitations=[],
                    )
                ],
                recommendations=[item],
            )
        ],
        prioritized_recommendations=[item],
        execution_requested=False,
    )


def test_calculated_metrics_are_deterministic() -> None:
    calculated = {
        item.name.value: item.value
        for item in calculate_campaign_metrics(valid_evidence())
    }

    assert calculated["ctr_percent"] == Decimal("10.0000")
    assert calculated["cpc"] == Decimal("5.0000")
    assert calculated["cvr_percent"] == Decimal("10.0000")
    assert calculated["cpa"] == Decimal("50.0000")
    assert calculated["roas"] == Decimal("4.0000")


def test_clicks_above_impressions_fail_validation() -> None:
    evidence = valid_evidence()
    evidence.metrics[MetricName.CLICKS] = metric(
        "1200",
        "metric-clicks",
    )

    validation = validate_campaign_evidence(evidence)

    assert validation.passed is False
    assert any(issue.code == "clicks_exceed_impressions" for issue in validation.issues)


def test_report_rejects_unknown_evidence_reference() -> None:
    report = valid_report()
    report.specialist_assessments[0].findings[0].evidence_ids = ["invented-metric"]

    validation = validate_expert_report(
        report,
        valid_evidence(),
    )

    assert validation.passed is False
    assert any(
        issue.code == "unknown_evidence_reference" for issue in validation.issues
    )


def test_shadow_report_rejects_execution_request() -> None:
    report = valid_report()
    report.execution_requested = True

    validation = validate_expert_report(
        report,
        valid_evidence(),
    )

    assert validation.passed is False
    assert any(issue.code == "execution_requested" for issue in validation.issues)


def test_human_expert_label_requires_matching_approval() -> None:
    report = valid_report()

    assert review_label(report, None) == (
        "Expert framework applied ? human review required"
    )

    review = HumanReview(
        report_hash=report_digest(report),
        reviewer_id="reviewer-123",
        reviewer_role="Senior Paid Media Strategist",
        decision=ReviewDecision.APPROVED,
        comments="Evidence and recommendations reviewed.",
        rubric_version=report.rubric_version,
        reviewed_at=datetime.now(UTC),
    )

    assert review_label(report, review) == "Human expert vetted"


def test_changed_report_invalidates_human_approval() -> None:
    report = valid_report()

    review = HumanReview(
        report_hash=report_digest(report),
        reviewer_id="reviewer-123",
        reviewer_role="Senior Paid Media Strategist",
        decision=ReviewDecision.APPROVED,
        rubric_version=report.rubric_version,
    )

    report.executive_summary = "This report changed after human approval."

    assert review_label(report, review) == (
        "Expert framework applied ? human review invalidated"
    )
