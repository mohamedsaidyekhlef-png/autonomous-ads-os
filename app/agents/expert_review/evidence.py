from decimal import ROUND_HALF_UP, Decimal

from app.agents.expert_review.schemas import (
    CalculatedMetric,
    CalculatedMetricName,
    CampaignEvidence,
    MetricName,
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
)

FOUR_PLACES = Decimal("0.0001")
ONE_HUNDRED = Decimal(100)


def rounded(value: Decimal) -> Decimal:
    return value.quantize(
        FOUR_PLACES,
        rounding=ROUND_HALF_UP,
    )


def metric_value(
    evidence: CampaignEvidence,
    name: MetricName,
) -> Decimal | None:
    datum = evidence.metrics.get(name)
    return datum.value if datum is not None else None


def metric_evidence_ids(
    evidence: CampaignEvidence,
    names: list[MetricName],
) -> list[str]:
    return [
        datum.evidence_id
        for name in names
        if (datum := evidence.metrics.get(name)) is not None
    ]


def calculated(
    *,
    name: CalculatedMetricName,
    numerator: Decimal | None,
    denominator: Decimal | None,
    multiplier: Decimal,
    formula: str,
    evidence_ids: list[str],
) -> CalculatedMetric:
    available = numerator is not None and denominator is not None and denominator > 0

    value = rounded((numerator / denominator) * multiplier) if available else None

    return CalculatedMetric(
        name=name,
        value=value,
        formula=formula,
        evidence_ids=evidence_ids,
        available=available,
    )


def calculate_campaign_metrics(
    evidence: CampaignEvidence,
) -> list[CalculatedMetric]:
    impressions = metric_value(
        evidence,
        MetricName.IMPRESSIONS,
    )
    clicks = metric_value(evidence, MetricName.CLICKS)
    spend = metric_value(evidence, MetricName.SPEND)
    conversions = metric_value(
        evidence,
        MetricName.CONVERSIONS,
    )
    revenue = metric_value(evidence, MetricName.REVENUE)

    return [
        calculated(
            name=CalculatedMetricName.CTR_PERCENT,
            numerator=clicks,
            denominator=impressions,
            multiplier=ONE_HUNDRED,
            formula="clicks / impressions * 100",
            evidence_ids=metric_evidence_ids(
                evidence,
                [MetricName.CLICKS, MetricName.IMPRESSIONS],
            ),
        ),
        calculated(
            name=CalculatedMetricName.CPC,
            numerator=spend,
            denominator=clicks,
            multiplier=Decimal(1),
            formula="spend / clicks",
            evidence_ids=metric_evidence_ids(
                evidence,
                [MetricName.SPEND, MetricName.CLICKS],
            ),
        ),
        calculated(
            name=CalculatedMetricName.CVR_PERCENT,
            numerator=conversions,
            denominator=clicks,
            multiplier=ONE_HUNDRED,
            formula="conversions / clicks * 100",
            evidence_ids=metric_evidence_ids(
                evidence,
                [
                    MetricName.CONVERSIONS,
                    MetricName.CLICKS,
                ],
            ),
        ),
        calculated(
            name=CalculatedMetricName.CPA,
            numerator=spend,
            denominator=conversions,
            multiplier=Decimal(1),
            formula="spend / conversions",
            evidence_ids=metric_evidence_ids(
                evidence,
                [
                    MetricName.SPEND,
                    MetricName.CONVERSIONS,
                ],
            ),
        ),
        calculated(
            name=CalculatedMetricName.ROAS,
            numerator=revenue,
            denominator=spend,
            multiplier=Decimal(1),
            formula="revenue / spend",
            evidence_ids=metric_evidence_ids(
                evidence,
                [MetricName.REVENUE, MetricName.SPEND],
            ),
        ),
    ]


def validate_campaign_evidence(
    evidence: CampaignEvidence,
) -> ValidationResult:
    issues: list[ValidationIssue] = []

    impressions = metric_value(
        evidence,
        MetricName.IMPRESSIONS,
    )
    clicks = metric_value(evidence, MetricName.CLICKS)
    spend = metric_value(evidence, MetricName.SPEND)
    conversions = metric_value(
        evidence,
        MetricName.CONVERSIONS,
    )
    revenue = metric_value(evidence, MetricName.REVENUE)

    evidence_ids = [item.id for item in evidence.evidence] + [
        datum.evidence_id for datum in evidence.metrics.values()
    ]

    duplicate_ids = {
        item_id for item_id in evidence_ids if evidence_ids.count(item_id) > 1
    }

    for duplicate_id in sorted(duplicate_ids):
        issues.append(
            ValidationIssue(
                code="duplicate_evidence_id",
                level=ValidationLevel.ERROR,
                message=(f"Evidence ID {duplicate_id!r} is not unique."),
                path="evidence",
            )
        )

    if impressions is not None and clicks is not None and clicks > impressions:
        issues.append(
            ValidationIssue(
                code="clicks_exceed_impressions",
                level=ValidationLevel.ERROR,
                message=(
                    "Clicks cannot exceed impressions for this "
                    "campaign-level evidence package."
                ),
                path="metrics.clicks",
            )
        )

    if clicks is not None and conversions is not None and conversions > clicks:
        issues.append(
            ValidationIssue(
                code="conversions_exceed_clicks",
                level=ValidationLevel.WARNING,
                message=(
                    "Conversions exceed clicks. Verify attribution, "
                    "view-through conversions, and duplicate events."
                ),
                path="metrics.conversions",
            )
        )

    if (spend is not None or revenue is not None) and not evidence.currency:
        issues.append(
            ValidationIssue(
                code="missing_currency",
                level=ValidationLevel.ERROR,
                message=(
                    "Currency is required when spend or revenue evidence is supplied."
                ),
                path="currency",
            )
        )

    if (
        evidence.date_start is not None
        and evidence.date_end is not None
        and evidence.date_end < evidence.date_start
    ):
        issues.append(
            ValidationIssue(
                code="invalid_date_range",
                level=ValidationLevel.ERROR,
                message=("The reporting end date cannot occur before the start date."),
                path="date_end",
            )
        )

    errors = [issue for issue in issues if issue.level == ValidationLevel.ERROR]

    return ValidationResult(
        passed=not errors,
        issues=issues,
    )
