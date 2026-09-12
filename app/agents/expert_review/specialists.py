from collections.abc import Callable

from app.agents.expert_review.schemas import (
    CampaignEvidence,
    Finding,
    MetricName,
    Provenance,
    Recommendation,
    Severity,
    SpecialistAssessment,
)
from app.agents.expert_review.state import ExpertReviewState


def evidence_ids(
    evidence: CampaignEvidence,
    metric_names: list[MetricName],
) -> list[str]:
    selected = [
        datum.evidence_id
        for name in metric_names
        if (datum := evidence.metrics.get(name)) is not None
    ]

    if selected:
        return selected

    return [item.id for item in evidence.evidence[:3]]


def assessment(
    *,
    agent_id: str,
    role_name: str,
    evidence: CampaignEvidence,
    metric_names: list[MetricName],
    finding_title: str,
    observation: str,
    significance: str,
    recommendation_title: str,
    rationale: str,
    expected_impact: str,
    measurement_plan: str,
    risk: Severity,
) -> SpecialistAssessment:
    references = evidence_ids(
        evidence,
        metric_names,
    )

    missing_information = []

    if not references:
        missing_information.append("No supporting campaign evidence was supplied.")

    return SpecialistAssessment(
        agent_id=agent_id,
        role_name=role_name,
        findings=[
            Finding(
                title=finding_title,
                observation=observation,
                significance=significance,
                severity=risk,
                basis=(Provenance.ACTUAL if references else Provenance.UNKNOWN),
                evidence_ids=references,
                confidence=0.8 if references else 0.2,
                limitations=(
                    []
                    if references
                    else ["The finding cannot be confirmed without campaign evidence."]
                ),
            )
        ],
        recommendations=[
            Recommendation(
                title=recommendation_title,
                rationale=rationale,
                expected_impact=expected_impact,
                measurement_plan=measurement_plan,
                risk=risk,
                confidence=0.75 if references else 0.2,
                evidence_ids=references,
                reversible=True,
                requires_human_approval=True,
            )
        ],
        missing_information=missing_information,
        conflicts=[],
    )


def measurement_auditor(
    state: ExpertReviewState,
) -> dict[str, object]:
    evidence = state["evidence"]

    result = assessment(
        agent_id="measurement_auditor",
        role_name="Measurement and Tracking Auditor",
        evidence=evidence,
        metric_names=[
            MetricName.IMPRESSIONS,
            MetricName.CLICKS,
            MetricName.SPEND,
            MetricName.CONVERSIONS,
            MetricName.REVENUE,
        ],
        finding_title="Measurement evidence review",
        observation=(
            "Campaign conclusions must remain bounded by the "
            "supplied impression, click, spend, conversion, and "
            "revenue evidence."
        ),
        significance=(
            "Optimization recommendations are unreliable when "
            "conversion or revenue evidence is incomplete."
        ),
        recommendation_title="Verify conversion measurement",
        rationale=(
            "Confirm conversion definitions, attribution windows, "
            "duplicate-event handling, and revenue completeness."
        ),
        expected_impact=(
            "Improved confidence in CPA and ROAS decisions; "
            "performance impact is not guaranteed."
        ),
        measurement_plan=(
            "Reconcile platform conversions with the system of "
            "record before approving budget changes."
        ),
        risk=Severity.HIGH,
    )

    return {
        "specialist_assessments": [result],
    }


def budget_controller(
    state: ExpertReviewState,
) -> dict[str, object]:
    evidence = state["evidence"]

    result = assessment(
        agent_id="budget_controller",
        role_name="Budget and Capital Controller",
        evidence=evidence,
        metric_names=[
            MetricName.SPEND,
            MetricName.CONVERSIONS,
            MetricName.REVENUE,
        ],
        finding_title="Budget efficiency review",
        observation=(
            "Spend efficiency should be evaluated against verified "
            "conversion and revenue outcomes."
        ),
        significance=(
            "Budget movement without reliable unit economics can increase waste."
        ),
        recommendation_title="Keep budget changes gated",
        rationale=(
            "Review CPA, ROAS, conversion quality, and statistical "
            "volume before reallocating spend."
        ),
        expected_impact=("Reduced downside from premature budget changes."),
        measurement_plan=(
            "Monitor spend, qualified conversions, CPA, ROAS, and "
            "conversion lag during an approved test window."
        ),
        risk=Severity.HIGH,
    )

    return {
        "specialist_assessments": [result],
    }


def campaign_strategist(
    state: ExpertReviewState,
) -> dict[str, object]:
    evidence = state["evidence"]

    result = assessment(
        agent_id="chief_strategy",
        role_name="Chief Performance Strategist",
        evidence=evidence,
        metric_names=[
            MetricName.IMPRESSIONS,
            MetricName.CLICKS,
            MetricName.CONVERSIONS,
        ],
        finding_title="Campaign strategy review",
        observation=(
            "Traffic and conversion evidence should determine "
            "whether the primary issue is reach, relevance, or "
            "post-click performance."
        ),
        significance=(
            "Changing targeting, creative, and landing pages "
            "simultaneously would make learning unreliable."
        ),
        recommendation_title="Use a controlled test sequence",
        rationale=(
            "Prioritize one measurable hypothesis at a time and "
            "preserve a stable comparison baseline."
        ),
        expected_impact=(
            "Clearer causal learning and lower risk of uncontrolled "
            "performance changes."
        ),
        measurement_plan=(
            "Pre-register the primary metric, guardrails, duration, "
            "and rollback threshold."
        ),
        risk=Severity.MEDIUM,
    )

    return {
        "specialist_assessments": [result],
    }


def risk_controller(
    state: ExpertReviewState,
) -> dict[str, object]:
    evidence = state["evidence"]

    result = assessment(
        agent_id="risk_controller",
        role_name="Advertising Risk Controller",
        evidence=evidence,
        metric_names=[
            MetricName.SPEND,
            MetricName.CONVERSIONS,
            MetricName.REVENUE,
        ],
        finding_title="Execution risk review",
        observation=(
            "The analysis is operating in Shadow Mode and has no "
            "authority to mutate campaigns or spend."
        ),
        significance=(
            "Recommendations must be reviewed before any external advertising action."
        ),
        recommendation_title="Require human approval",
        rationale=(
            "A qualified reviewer should confirm evidence, policy "
            "compliance, and commercial assumptions."
        ),
        expected_impact=("Reduced risk of unsupported or harmful campaign changes."),
        measurement_plan=(
            "Record reviewer identity, decision, rubric version, "
            "timestamp, and immutable report hash."
        ),
        risk=Severity.CRITICAL,
    )

    return {
        "specialist_assessments": [result],
    }


SpecialistNode = Callable[
    [ExpertReviewState],
    dict[str, object],
]

SPECIALIST_NODES: dict[str, SpecialistNode] = {
    "measurement_auditor": measurement_auditor,
    "budget_controller": budget_controller,
    "campaign_strategist": campaign_strategist,
    "risk_controller": risk_controller,
}
