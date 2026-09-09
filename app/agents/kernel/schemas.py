from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AgentRisk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceStrength(StrEnum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERIFIED = "verified"


class ActionDisposition(StrEnum):
    PROPOSE = "propose"
    NO_ACTION = "no_action"
    REQUEST_DATA = "request_data"
    EMERGENCY_STOP = "emergency_stop"


class AgentProfile(StrictModel):
    id: str
    name: str
    department: str
    mission: str
    professional_standard: str

    responsibilities: list[str]
    expertise: list[str]
    tools: list[str]
    prohibited_behaviors: list[str]
    evaluation_criteria: list[str]

    default_review_minutes: int = Field(ge=5, le=10080)
    maximum_action_risk: AgentRisk


class Evidence(StrictModel):
    statement: str = Field(min_length=3, max_length=1500)
    source: str = Field(min_length=1, max_length=200)
    source_id: str | None = Field(default=None, max_length=300)
    observed_at: datetime | None = None
    confidence: float = Field(ge=0, le=1)
    strength: EvidenceStrength
    freshness_minutes: int | None = Field(default=None, ge=0)


class Observation(StrictModel):
    statement: str = Field(min_length=3, max_length=1500)
    significance: str = Field(min_length=3, max_length=1000)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class Hypothesis(StrictModel):
    statement: str = Field(min_length=3, max_length=1500)
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    falsification_test: str = Field(min_length=3, max_length=1000)


class ActionAlternative(StrictModel):
    action_type: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=3, max_length=1500)

    expected_benefit: str = Field(min_length=3, max_length=1000)
    possible_downside: str = Field(min_length=3, max_length=1000)

    reversible: bool
    estimated_risk: AgentRisk
    confidence: float = Field(ge=0, le=1)

    required_tools: list[str] = Field(default_factory=list)
    required_conditions: list[str] = Field(default_factory=list)


class ProposedAction(StrictModel):
    disposition: ActionDisposition
    action_type: str = Field(min_length=1, max_length=100)

    platform: str | None = Field(default=None, max_length=50)
    account_id: str | None = Field(default=None, max_length=255)
    target_type: str | None = Field(default=None, max_length=100)
    target_id: str | None = Field(default=None, max_length=255)

    parameters: dict[str, Any] = Field(default_factory=dict)

    rationale: str = Field(min_length=3, max_length=2000)
    expected_effect: str = Field(min_length=3, max_length=1000)

    reversible: bool
    rollback_condition: str = Field(min_length=3, max_length=1000)

    confidence: float = Field(ge=0, le=1)
    risk: AgentRisk


class MeasurementPlan(StrictModel):
    primary_metric: str = Field(min_length=1, max_length=200)
    guardrail_metrics: list[str] = Field(default_factory=list)

    earliest_evaluation_minutes: int = Field(ge=5)
    final_evaluation_minutes: int = Field(ge=5)

    success_condition: str = Field(min_length=3, max_length=1000)
    failure_condition: str = Field(min_length=3, max_length=1000)

    @model_validator(mode="after")
    def validate_evaluation_window(self) -> "MeasurementPlan":
        if self.final_evaluation_minutes < self.earliest_evaluation_minutes:
            raise ValueError(
                "Final evaluation cannot occur before earliest evaluation."
            )

        return self


class AgentDecision(StrictModel):
    decision_id: str = Field(min_length=8, max_length=200)
    agent_id: str = Field(min_length=2, max_length=100)
    objective: str = Field(min_length=3, max_length=1500)

    data_quality_assessment: str = Field(min_length=3, max_length=1500)
    observations: list[Observation]
    hypotheses: list[Hypothesis]
    alternatives: list[ActionAlternative]

    selected_action: ProposedAction

    assumptions: list[str]
    risks: list[str]
    policy_questions: list[str]

    concise_rationale: str = Field(min_length=3, max_length=2000)
    overall_confidence: float = Field(ge=0, le=1)

    measurement_plan: MeasurementPlan
    next_review_minutes: int = Field(ge=5, le=10080)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentTask(StrictModel):
    objective: str = Field(min_length=3, max_length=1500)

    organization_id: str
    advertising_account_ids: list[str] = Field(default_factory=list)

    business_context: dict[str, Any] = Field(default_factory=dict)
    calculated_metrics: dict[str, Any] = Field(default_factory=dict)

    evidence: list[Evidence] = Field(default_factory=list)
    recent_changes: list[dict[str, Any]] = Field(default_factory=list)
    active_experiments: list[dict[str, Any]] = Field(default_factory=list)
    relevant_memories: list[dict[str, Any]] = Field(default_factory=list)

    hard_constraints: list[str] = Field(default_factory=list)
    available_tools: list[str] = Field(default_factory=list)

    requested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
