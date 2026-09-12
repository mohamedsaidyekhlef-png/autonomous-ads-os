import operator
from typing import Annotated, TypedDict

from app.agents.expert_review.schemas import (
    CalculatedMetric,
    CampaignEvidence,
    ExpertAnalysisReport,
    HumanReview,
    SpecialistAssessment,
    ValidationResult,
)


class ExpertReviewState(TypedDict, total=False):
    run_id: str
    evidence: CampaignEvidence
    calculated_metrics: list[CalculatedMetric]
    specialist_assessments: Annotated[
        list[SpecialistAssessment],
        operator.add,
    ]
    draft_report: ExpertAnalysisReport
    validation: ValidationResult
    human_review: HumanReview
    status: str
    error: str
