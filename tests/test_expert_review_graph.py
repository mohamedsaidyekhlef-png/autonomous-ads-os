from decimal import Decimal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.agents.expert_review.graph import (
    build_expert_review_graph,
)
from app.agents.expert_review.schemas import (
    CampaignEvidence,
    MetricDatum,
    MetricName,
    Provenance,
)


def evidence() -> CampaignEvidence:
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

    return CampaignEvidence(
        objective="Generate qualified B2B software leads.",
        currency="USD",
        metrics={
            MetricName.IMPRESSIONS: metric(
                "10000",
                "metric-impressions",
            ),
            MetricName.CLICKS: metric(
                "800",
                "metric-clicks",
            ),
            MetricName.SPEND: metric(
                "3000",
                "metric-spend",
            ),
            MetricName.CONVERSIONS: metric(
                "40",
                "metric-conversions",
            ),
            MetricName.REVENUE: metric(
                "12000",
                "metric-revenue",
            ),
        },
    )


def test_graph_pauses_for_human_review() -> None:
    graph = build_expert_review_graph(
        checkpointer=InMemorySaver(),
    )
    config = {
        "configurable": {
            "thread_id": "run-human-review-1",
        }
    }

    result = graph.invoke(
        {
            "run_id": "run-human-review-1",
            "evidence": evidence(),
            "specialist_assessments": [],
            "status": "queued",
        },
        config=config,
    )

    assert result["status"] == "awaiting_human_review"
    assert result["draft_report"].automated_validation_passed is True
    assert len(result["specialist_assessments"]) == 4
    assert "__interrupt__" in result


def test_graph_resumes_after_human_approval() -> None:
    graph = build_expert_review_graph(
        checkpointer=InMemorySaver(),
    )
    config = {
        "configurable": {
            "thread_id": "run-human-review-2",
        }
    }

    first_result = graph.invoke(
        {
            "run_id": "run-human-review-2",
            "evidence": evidence(),
            "specialist_assessments": [],
            "status": "queued",
        },
        config=config,
    )

    assert "__interrupt__" in first_result

    completed = graph.invoke(
        Command(
            resume={
                "decision": "approved",
                "reviewer_id": "reviewer-123",
                "reviewer_role": ("Senior Paid Media Strategist"),
                "comments": ("Evidence, risks, and recommendations reviewed."),
            }
        ),
        config=config,
    )

    assert completed["status"] == "completed"
    assert completed["human_review"].decision.value == "approved"


def test_invalid_evidence_stops_before_specialists() -> None:
    invalid = evidence()
    invalid.metrics[MetricName.CLICKS] = MetricDatum(
        value=Decimal(20000),
        provenance=Provenance.ACTUAL,
        evidence_id="metric-clicks",
        source="uploaded_campaign_csv",
    )

    graph = build_expert_review_graph()

    result = graph.invoke(
        {
            "run_id": "run-invalid-evidence",
            "evidence": invalid,
            "specialist_assessments": [],
            "status": "queued",
        }
    )

    assert result["status"] == "failed_evidence_validation"
    assert result["validation"].passed is False
    assert result["specialist_assessments"] == []
    assert "draft_report" not in result


def test_human_rejection_does_not_complete_report() -> None:
    graph = build_expert_review_graph(
        checkpointer=InMemorySaver(),
    )
    config = {
        "configurable": {
            "thread_id": "run-human-review-3",
        }
    }

    graph.invoke(
        {
            "run_id": "run-human-review-3",
            "evidence": evidence(),
            "specialist_assessments": [],
            "status": "queued",
        },
        config=config,
    )

    rejected = graph.invoke(
        Command(
            resume={
                "decision": "rejected",
                "reviewer_id": "reviewer-123",
                "reviewer_role": ("Senior Paid Media Strategist"),
                "comments": "Recommendation requires revision.",
            }
        ),
        config=config,
    )

    assert rejected["status"] == "rejected"
