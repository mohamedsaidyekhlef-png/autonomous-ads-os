from decimal import Decimal
from typing import Any

from app.agents.expert_review.evidence import (
    calculate_campaign_metrics,
)
from app.agents.expert_review.groq_runner import (
    GroqSpecialistRunner,
    build_specialist_system_prompt,
)
from app.agents.expert_review.schemas import (
    CampaignEvidence,
    MetricDatum,
    MetricName,
    Provenance,
)
from app.agents.expert_review.state import ExpertReviewState


class FakeStructuredModel:
    def __init__(self) -> None:
        self.messages: list[Any] = []

    def invoke(
        self,
        messages: list[Any],
    ) -> dict[str, Any]:
        self.messages = messages

        return {
            "agent_id": "incorrect-model-agent",
            "role_name": "Incorrect model role",
            "findings": [
                {
                    "title": "Verified spend evidence",
                    "observation": (
                        "The supplied campaign includes spend and conversion evidence."
                    ),
                    "significance": (
                        "Budget decisions should use verified conversion outcomes."
                    ),
                    "severity": "medium",
                    "basis": "actual",
                    "evidence_ids": [
                        "metric-spend",
                        "metric-conversions",
                    ],
                    "confidence": 0.8,
                    "limitations": [],
                }
            ],
            "recommendations": [
                {
                    "title": "Review conversion efficiency",
                    "rationale": (
                        "Spend and conversion evidence supports "
                        "a controlled efficiency review."
                    ),
                    "expected_impact": (
                        "Potential efficiency improvement; results are not guaranteed."
                    ),
                    "measurement_plan": ("Monitor CPA and qualified conversions."),
                    "risk": "medium",
                    "confidence": 0.75,
                    "evidence_ids": [
                        "metric-spend",
                        "metric-conversions",
                    ],
                    "reversible": True,
                    "requires_human_approval": False,
                }
            ],
            "missing_information": [],
            "conflicts": [],
        }


class FakeChatModel:
    def __init__(self) -> None:
        self.structured = FakeStructuredModel()
        self.schema: Any = None
        self.method: str | None = None

    def with_structured_output(
        self,
        schema: Any,
        *,
        method: str,
    ) -> FakeStructuredModel:
        self.schema = schema
        self.method = method
        return self.structured


def evidence() -> CampaignEvidence:
    return CampaignEvidence(
        objective="Improve qualified lead efficiency.",
        currency="USD",
        metrics={
            MetricName.SPEND: MetricDatum(
                value=Decimal(3000),
                provenance=Provenance.ACTUAL,
                evidence_id="metric-spend",
                source="uploaded_campaign_csv",
            ),
            MetricName.CONVERSIONS: MetricDatum(
                value=Decimal(40),
                provenance=Provenance.ACTUAL,
                evidence_id="metric-conversions",
                source="uploaded_campaign_csv",
            ),
        },
    )


def test_groq_runner_enforces_identity_and_human_review() -> None:
    model = FakeChatModel()
    runner = GroqSpecialistRunner(model=model)
    campaign_evidence = evidence()

    state: ExpertReviewState = {
        "run_id": "run-groq-test-1",
        "evidence": campaign_evidence,
        "calculated_metrics": calculate_campaign_metrics(campaign_evidence),
        "specialist_assessments": [],
        "status": "metrics_calculated",
    }

    result = runner(
        state,
        "measurement_auditor",
    )
    assessment = result["specialist_assessments"][0]

    assert assessment.agent_id == "measurement_auditor"
    assert assessment.role_name == ("Measurement and Tracking Auditor")
    assert all(item.requires_human_approval for item in assessment.recommendations)
    assert model.method == "function_calling"
    assert len(model.structured.messages) == 2


def test_specialist_prompt_contains_non_fabrication_rules() -> None:
    prompt = build_specialist_system_prompt("budget_controller")

    assert "Never invent metrics" in prompt
    assert "Every factual finding must cite" in prompt
    assert "Shadow Mode" in prompt
    assert "Every recommendation requires human approval" in prompt
