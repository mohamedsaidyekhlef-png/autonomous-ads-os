from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Provenance(StrEnum):
    ACTUAL = "actual"
    CALCULATED = "calculated"
    USER_SUPPLIED = "user_supplied"
    AI_ESTIMATE = "ai_estimate"
    UNKNOWN = "unknown"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationLevel(StrEnum):
    WARNING = "warning"
    ERROR = "error"


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"


class MetricName(StrEnum):
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    SPEND = "spend"
    CONVERSIONS = "conversions"
    REVENUE = "revenue"


class CalculatedMetricName(StrEnum):
    CTR_PERCENT = "ctr_percent"
    CPC = "cpc"
    CVR_PERCENT = "cvr_percent"
    CPA = "cpa"
    ROAS = "roas"


class MetricDatum(StrictModel):
    value: Decimal = Field(ge=0)
    provenance: Provenance
    evidence_id: str = Field(min_length=3, max_length=200)
    source: str = Field(min_length=2, max_length=200)
    observed_at: datetime | None = None


class EvidenceItem(StrictModel):
    id: str = Field(min_length=3, max_length=200)
    statement: str = Field(min_length=3, max_length=2000)
    source: str = Field(min_length=2, max_length=200)
    provenance: Provenance
    observed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CampaignEvidence(StrictModel):
    objective: str = Field(min_length=3, max_length=2000)
    mode: Literal["shadow"] = "shadow"
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    date_start: datetime | None = None
    date_end: datetime | None = None
    metrics: dict[MetricName, MetricDatum] = Field(default_factory=dict)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_currency(self) -> "CampaignEvidence":
        if self.currency:
            self.currency = self.currency.upper()
        return self


class CalculatedMetric(StrictModel):
    name: CalculatedMetricName
    value: Decimal | None
    formula: str
    provenance: Literal[Provenance.CALCULATED] = Provenance.CALCULATED
    evidence_ids: list[str]
    available: bool


class Finding(StrictModel):
    title: str = Field(min_length=3, max_length=300)
    observation: str = Field(min_length=3, max_length=2000)
    significance: str = Field(min_length=3, max_length=1500)
    severity: Severity
    basis: Provenance
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_estimate_limitations(self) -> "Finding":
        if self.basis == Provenance.AI_ESTIMATE and not self.limitations:
            raise ValueError("AI estimates must disclose at least one limitation.")
        return self


class Recommendation(StrictModel):
    title: str = Field(min_length=3, max_length=300)
    rationale: str = Field(min_length=3, max_length=2000)
    expected_impact: str = Field(min_length=3, max_length=1000)
    measurement_plan: str = Field(min_length=3, max_length=1500)
    risk: Severity
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)
    reversible: bool
    requires_human_approval: bool = True


class SpecialistAssessment(StrictModel):
    agent_id: str = Field(min_length=2, max_length=100)
    role_name: str = Field(min_length=2, max_length=200)
    findings: list[Finding]
    recommendations: list[Recommendation]
    missing_information: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)


class ExpertAnalysisReport(StrictModel):
    run_id: str = Field(min_length=8, max_length=200)
    rubric_version: str = Field(min_length=3, max_length=100)
    mode: Literal["shadow"] = "shadow"
    executive_summary: str = Field(min_length=3, max_length=5000)
    data_quality_score: float = Field(ge=0, le=1)
    specialist_assessments: list[SpecialistAssessment]
    prioritized_recommendations: list[Recommendation]
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    execution_requested: bool = False
    automated_validation_passed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ValidationIssue(StrictModel):
    code: str = Field(min_length=2, max_length=100)
    level: ValidationLevel
    message: str = Field(min_length=3, max_length=1000)
    path: str = Field(min_length=1, max_length=500)


class ValidationResult(StrictModel):
    passed: bool
    issues: list[ValidationIssue]
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HumanReview(StrictModel):
    report_hash: str = Field(min_length=64, max_length=64)
    reviewer_id: str = Field(min_length=3, max_length=200)
    reviewer_role: str = Field(min_length=3, max_length=200)
    decision: ReviewDecision
    comments: str = Field(default="", max_length=5000)
    rubric_version: str = Field(min_length=3, max_length=100)
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
