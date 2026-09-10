# ruff: noqa: B008
"""Organization-scoped operational records; all mutations remain drafts/shadow-only."""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.core.auth import OrganizationContext, require_organization_context
from app.database.models import (
    AgentDecisionRecord,
    CampaignRecord,
    CreativeAssetRecord,
    ExperimentRecord,
    Organization,
    OrganizationSettingRecord,
    ReportRecord,
)
from app.database.session import SessionLocal

router = APIRouter(prefix="/v1", tags=["Organization data"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CampaignInput(StrictModel):
    name: str = Field(min_length=2, max_length=255)
    platform: str = "local_demo"
    objective: str = "conversions"
    daily_budget_minor: int = Field(default=0, ge=0)


class ExperimentInput(StrictModel):
    name: str
    hypothesis: str
    primary_metric: str


class CreativeInput(StrictModel):
    name: str
    platform: str = "local_demo"
    prompt: str


class ReportInput(StrictModel):
    report_type: str = "daily"
    summary: str = "Shadow report: no live platform data has been imported."


class SettingInput(StrictModel):
    value: dict[str, Any]


def _rows(model: Any, org_id: uuid.UUID) -> list[Any]:
    with SessionLocal() as database:
        return database.scalars(
            select(model)
            .where(model.organization_id == org_id)
            .order_by(model.created_at.desc())
            .limit(100)
        ).all()


@router.get("/overview")
def overview(
    context: OrganizationContext = Depends(require_organization_context),
) -> dict[str, Any]:
    with SessionLocal() as database:
        org = database.get(Organization, context.organization_id)
        if org is None:
            raise HTTPException(404, "Organization was not found.")
        campaigns = _rows(CampaignRecord, context.organization_id)
        return {
            "organization": {
                "id": str(org.id),
                "name": org.name,
                "currency": org.currency,
                "risk_profile": org.risk_profile,
            },
            "shadow_mode": True,
            "dry_run": True,
            "campaigns": len(campaigns),
            "decisions": len(_rows(AgentDecisionRecord, context.organization_id)),
            "experiments": len(_rows(ExperimentRecord, context.organization_id)),
            "creatives": len(_rows(CreativeAssetRecord, context.organization_id)),
            "reports": len(_rows(ReportRecord, context.organization_id)),
            "live_platform_actions": False,
        }


@router.get("/campaigns")
def campaigns(
    context: OrganizationContext = Depends(require_organization_context),
) -> list[dict[str, Any]]:
    return [
        {
            "id": str(x.id),
            "name": x.name,
            "platform": x.platform,
            "status": x.status,
            "objective": x.objective,
            "daily_budget_minor": x.daily_budget_minor,
            "currency": x.currency,
            "configuration": x.configuration,
            "metrics": x.metrics,
        }
        for x in _rows(CampaignRecord, context.organization_id)
    ]


@router.post("/campaigns", status_code=201)
def create_campaign(
    payload: CampaignInput,
    context: OrganizationContext = Depends(require_organization_context),
) -> dict[str, Any]:
    with SessionLocal() as database:
        org = database.get(Organization, context.organization_id)
        campaign = CampaignRecord(
            organization_id=context.organization_id,
            name=payload.name,
            platform=payload.platform,
            objective=payload.objective,
            status="draft",
            daily_budget_minor=payload.daily_budget_minor,
            currency=org.currency if org else "USD",
            configuration={"shadow_mode": True},
            metrics={},
        )
        database.add(campaign)
        database.commit()
        database.refresh(campaign)
        return {"id": str(campaign.id), "status": "draft", "shadow_mode": True}


@router.get("/decisions")
def decisions(
    context: OrganizationContext = Depends(require_organization_context),
) -> list[dict[str, Any]]:
    return [
        {
            "id": str(x.id),
            "agent_id": x.agent_id,
            "status": x.status,
            "objective": x.objective,
            "rationale": x.rationale,
            "confidence": x.confidence,
            "risk": x.risk,
            "proposed_actions": x.proposed_actions,
        }
        for x in _rows(AgentDecisionRecord, context.organization_id)
    ]


@router.get("/experiments")
def experiments(
    context: OrganizationContext = Depends(require_organization_context),
) -> list[dict[str, Any]]:
    return [
        {
            "id": str(x.id),
            "name": x.name,
            "hypothesis": x.hypothesis,
            "primary_metric": x.primary_metric,
            "status": x.status,
            "results": x.results,
        }
        for x in _rows(ExperimentRecord, context.organization_id)
    ]


@router.post("/experiments", status_code=201)
def create_experiment(
    payload: ExperimentInput,
    context: OrganizationContext = Depends(require_organization_context),
) -> dict[str, Any]:
    with SessionLocal() as database:
        item = ExperimentRecord(
            organization_id=context.organization_id,
            name=payload.name,
            hypothesis=payload.hypothesis,
            primary_metric=payload.primary_metric,
            status="draft",
            control_configuration={"shadow_mode": True},
            variant_configuration={},
            results={},
        )
        database.add(item)
        database.commit()
        database.refresh(item)
        return {"id": str(item.id), "status": "draft", "shadow_mode": True}


@router.get("/creatives")
def creatives(
    context: OrganizationContext = Depends(require_organization_context),
) -> list[dict[str, Any]]:
    return [
        {
            "id": str(x.id),
            "name": x.name,
            "platform": x.platform,
            "asset_type": x.asset_type,
            "status": x.status,
            "prompt": x.prompt,
            "content": x.content,
        }
        for x in _rows(CreativeAssetRecord, context.organization_id)
    ]


@router.post("/creatives", status_code=201)
def create_creative(
    payload: CreativeInput,
    context: OrganizationContext = Depends(require_organization_context),
) -> dict[str, Any]:
    with SessionLocal() as database:
        item = CreativeAssetRecord(
            organization_id=context.organization_id,
            name=payload.name,
            platform=payload.platform,
            asset_type="copy",
            status="draft",
            prompt=payload.prompt,
            content={"shadow_mode": True},
        )
        database.add(item)
        database.commit()
        database.refresh(item)
        return {"id": str(item.id), "status": "draft", "shadow_mode": True}


@router.get("/reports")
def reports(
    context: OrganizationContext = Depends(require_organization_context),
) -> list[dict[str, Any]]:
    return [
        {
            "id": str(x.id),
            "report_type": x.report_type,
            "status": x.status,
            "summary": x.summary,
            "metrics": x.metrics,
            "generated_at": x.generated_at.isoformat(),
        }
        for x in _rows(ReportRecord, context.organization_id)
    ]


@router.post("/reports", status_code=201)
def create_report(
    payload: ReportInput,
    context: OrganizationContext = Depends(require_organization_context),
) -> dict[str, Any]:
    now = datetime.now(UTC)
    with SessionLocal() as database:
        item = ReportRecord(
            organization_id=context.organization_id,
            report_type=payload.report_type,
            status="generated",
            period_start=now,
            period_end=now,
            summary=payload.summary,
            metrics={"live_platform_data": False, "shadow_mode": True},
        )
        database.add(item)
        database.commit()
        database.refresh(item)
        return {"id": str(item.id), "status": item.status, "shadow_mode": True}


@router.get("/settings")
def settings(
    context: OrganizationContext = Depends(require_organization_context),
) -> list[dict[str, Any]]:
    return [
        {"key": x.key, "value": x.value}
        for x in _rows(OrganizationSettingRecord, context.organization_id)
    ]


@router.put("/settings/{key}")
def put_setting(
    key: str,
    payload: SettingInput,
    context: OrganizationContext = Depends(require_organization_context),
) -> dict[str, Any]:
    with SessionLocal() as database:
        item = database.scalars(
            select(OrganizationSettingRecord).where(
                OrganizationSettingRecord.organization_id == context.organization_id,
                OrganizationSettingRecord.key == key,
            )
        ).one_or_none()
        if item is None:
            item = OrganizationSettingRecord(
                organization_id=context.organization_id, key=key, value=payload.value
            )
            database.add(item)
        else:
            item.value = payload.value
        database.commit()
    return {"key": key, "value": payload.value, "shadow_mode": True}
