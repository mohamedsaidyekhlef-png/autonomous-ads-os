# ruff: noqa: B008
import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update

from app.agents.registry import get_agent_profile
from app.core.auth import OrganizationContext, require_organization_context
from app.database.models import (
    AgentDecisionRecord,
    AgentRun,
    CampaignRecord,
    Organization,
)
from app.database.session import SessionLocal
from app.llm.client import structured_completion
from app.workflows.queue import enqueue_run

router = APIRouter(prefix="/v1/command", tags=["Agent Command Center"])
DEFAULT_AGENTS = [
    "chief_strategy",
    "measurement_auditor",
    "budget_controller",
    "risk_controller",
]
SYSTEM_PROMPT = """You are the Chief Strategy Brain of Autonomous Ads OS. Return only JSON matching the supplied schema. This is mandatory shadow mode: analyze and create drafts only. Never claim platform actions or ad spend occurred. Mark assumptions and missing evidence clearly; recommend reversible actions and stop-losses."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CommandRequest(StrictModel):
    command: str = Field(min_length=5, max_length=4000)
    selected_agents: list[str] = Field(default_factory=lambda: list(DEFAULT_AGENTS))
    mode: Literal["shadow"] = "shadow"
    create_campaign_draft: bool = True


class Recommendation(StrictModel):
    title: str = Field(min_length=3, max_length=200)
    action_type: Literal[
        "analyze",
        "create_campaign",
        "update_campaign",
        "pause_campaign",
        "create_experiment",
        "create_creative",
        "fix_tracking",
        "adjust_budget",
        "request_information",
    ]
    rationale: str = Field(min_length=10)
    expected_impact: str = Field(min_length=3)
    risk: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0, le=1)
    measurement: str = Field(min_length=3)


class CommandResult(StrictModel):
    executive_summary: str = Field(min_length=10)
    interpretation: str = Field(min_length=5)
    verified_observations: list[str]
    assumptions: list[str]
    missing_information: list[str]
    diagnosis: list[str]
    recommendations: list[Recommendation] = Field(min_length=1, max_length=8)
    warnings: list[str]
    next_review_minutes: int = Field(ge=15, le=10080)


def validate_agents(agent_ids: list[str]) -> list[dict[str, Any]]:
    if not agent_ids:
        raise HTTPException(422, "Select at least one agent.")
    profiles = []
    for agent_id in dict.fromkeys(agent_ids):
        try:
            profiles.append(get_agent_profile(agent_id).model_dump(mode="json"))
        except KeyError as exc:
            raise HTTPException(422, f"Unknown agent: {agent_id}") from exc
    return profiles


def command_context(
    organization: Organization, profiles: list[dict[str, Any]]
) -> dict[str, Any]:
    with SessionLocal() as database:
        campaigns = database.scalars(
            select(CampaignRecord)
            .where(CampaignRecord.organization_id == organization.id)
            .order_by(CampaignRecord.updated_at.desc())
            .limit(25)
        ).all()
        return {
            "organization": {
                "id": str(organization.id),
                "name": organization.name,
                "currency": organization.currency,
                "risk_profile": organization.risk_profile,
                "daily_spend_cap_minor": organization.daily_spend_cap_minor,
                "monthly_spend_cap_minor": organization.monthly_spend_cap_minor,
                "automation_enabled": False,
            },
            "agents": profiles,
            "campaigns": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "platform": c.platform,
                    "status": c.status,
                    "objective": c.objective,
                    "daily_budget_minor": c.daily_budget_minor,
                    "currency": c.currency,
                    "metrics": c.metrics,
                }
                for c in campaigns
            ],
            "data_quality": {
                "source": "local_database",
                "live_platform_data": False,
                "tracking_verified": False,
                "execution_mode": "shadow",
            },
        }


async def run_llm(command: str, context: dict[str, Any]) -> CommandResult:
    content = await structured_completion(
        SYSTEM_PROMPT, command, context, CommandResult.model_json_schema()
    )
    return CommandResult.model_validate_json(content)


def serialize_run(
    run: AgentRun, decisions: list[AgentDecisionRecord] | None = None
) -> dict[str, Any]:
    now = datetime.now(UTC)
    end = run.completed_at or now
    elapsed = max(0, int((end - run.created_at).total_seconds()))
    payload: dict[str, Any] = {
        "id": str(run.id),
        "run_id": str(run.id),
        "status": run.status,
        "mode": run.mode,
        "objective": run.objective,
        "selected_agents": run.selected_agents,
        "result_summary": run.result_summary,
        "result": run.result_data,
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat(),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "elapsed_seconds": elapsed,
    }
    if decisions is not None:
        payload["decisions"] = [
            {
                "id": str(d.id),
                "agent_id": d.agent_id,
                "status": d.status,
                "rationale": d.rationale,
                "confidence": d.confidence,
                "risk": d.risk,
                "evidence": d.evidence,
                "proposed_actions": d.proposed_actions,
            }
            for d in decisions
        ]
    return payload


def process_run(run_id: uuid.UUID) -> None:
    """Worker entrypoint. Re-delivery is safe: only a queued run can start."""
    with SessionLocal() as database:
        claimed = database.execute(
            update(AgentRun)
            .where(AgentRun.id == run_id, AgentRun.status == "queued")
            .values(status="running", started_at=datetime.now(UTC), error_message=None)
        ).rowcount
        database.commit()
        if not claimed:
            return
        run = database.get(AgentRun, run_id)
        if run is None:
            return
        organization = database.get(Organization, run.organization_id)
        if organization is None:
            _fail_run(run_id, "Organization no longer exists.")
            return
        request = CommandRequest.model_validate(run.request_data)
        profiles = validate_agents(request.selected_agents)
        context = command_context(organization, profiles)
    try:
        result = asyncio.run(run_llm(request.command, context))
        _persist_result(run_id, result)
    except Exception as exc:  # noqa: BLE001 - worker must persist any terminal failure
        _fail_run(
            run_id,
            "Structured shadow decision could not be completed: " + str(exc)[:500],
        )


def _persist_result(run_id: uuid.UUID, result: CommandResult) -> None:
    with SessionLocal() as database:
        run = database.get(AgentRun, run_id)
        if run is None or run.status == "completed":
            return
        if run.status != "running":
            return
        organization = database.get(Organization, run.organization_id)
        if organization is None:
            raise RuntimeError("Organization no longer exists.")
        request = CommandRequest.model_validate(run.request_data)
        for recommendation in result.recommendations:
            database.add(
                AgentDecisionRecord(
                    organization_id=run.organization_id,
                    agent_run_id=run.id,
                    agent_id="chief_strategy",
                    status="proposed",
                    objective=request.command,
                    rationale=recommendation.rationale,
                    confidence=recommendation.confidence,
                    risk=recommendation.risk,
                    evidence=[
                        {
                            "source": "local_database",
                            "strength": "limited",
                            "live_platform_data": False,
                        }
                    ],
                    proposed_actions=[recommendation.model_dump(mode="json")],
                )
            )
            if (
                request.create_campaign_draft
                and recommendation.action_type == "create_campaign"
            ):
                database.add(
                    CampaignRecord(
                        organization_id=run.organization_id,
                        platform="local_demo",
                        name=recommendation.title,
                        objective="conversions",
                        status="draft",
                        daily_budget_minor=0,
                        currency=organization.currency,
                        configuration={
                            "source": "agent_command_center",
                            "agent_run_id": str(run.id),
                            "recommendation": recommendation.model_dump(mode="json"),
                            "shadow_mode": True,
                        },
                        metrics={},
                    )
                )
        run.status = "completed"
        run.result_summary = result.executive_summary
        run.result_data = result.model_dump(mode="json")
        run.completed_at = datetime.now(UTC)
        database.commit()


def _fail_run(run_id: uuid.UUID, message: str) -> None:
    with SessionLocal() as database:
        run = database.get(AgentRun, run_id)
        if run is not None and run.status not in {"completed", "failed"}:
            run.status = "failed"
            run.error_message = message
            run.completed_at = datetime.now(UTC)
            database.commit()


@router.post("/runs", status_code=202)
def create_command_run(
    request: CommandRequest,
    response: Response,
    context: OrganizationContext = Depends(require_organization_context),
    idempotency_key: str | None = Header(default=None),
) -> dict[str, Any]:
    validate_agents(request.selected_agents)
    with SessionLocal() as database:
        if idempotency_key:
            existing = database.scalars(
                select(AgentRun).where(
                    AgentRun.organization_id == context.organization_id,
                    AgentRun.idempotency_key == idempotency_key,
                )
            ).first()
            if existing:
                response.headers["Location"] = f"/v1/command/runs/{existing.id}"
                return {
                    "run_id": str(existing.id),
                    "status": existing.status,
                    "mode": "shadow",
                    "status_url": f"/v1/command/runs/{existing.id}",
                    "idempotent": True,
                }
        run = AgentRun(
            organization_id=context.organization_id,
            status="queued",
            mode="shadow",
            trigger_source="command_center",
            objective=request.command,
            selected_agents=request.selected_agents,
            request_data=request.model_dump(mode="json"),
            idempotency_key=idempotency_key,
        )
        database.add(run)
        database.commit()
        database.refresh(run)
        run_id = run.id
    try:
        enqueue_run(run_id)
    except RuntimeError as exc:
        _fail_run(run_id, str(exc))
        raise HTTPException(503, str(exc)) from exc
    response.headers["Location"] = f"/v1/command/runs/{run_id}"
    return {
        "run_id": str(run_id),
        "status": "queued",
        "mode": "shadow",
        "status_url": f"/v1/command/runs/{run_id}",
    }


@router.get("/runs")
def list_command_runs(
    context: OrganizationContext = Depends(require_organization_context),
) -> list[dict[str, Any]]:
    with SessionLocal() as database:
        runs = database.scalars(
            select(AgentRun)
            .where(AgentRun.organization_id == context.organization_id)
            .order_by(AgentRun.created_at.desc())
            .limit(50)
        ).all()
        return [serialize_run(run) for run in runs]


@router.get("/runs/{run_id}")
def get_command_run(
    run_id: uuid.UUID,
    context: OrganizationContext = Depends(require_organization_context),
) -> dict[str, Any]:
    with SessionLocal() as database:
        run = database.get(AgentRun, run_id)
        if run is None or run.organization_id != context.organization_id:
            raise HTTPException(404, "Agent run was not found.")
        decisions = database.scalars(
            select(AgentDecisionRecord)
            .where(AgentDecisionRecord.agent_run_id == run.id)
            .order_by(AgentDecisionRecord.created_at)
        ).all()
        return serialize_run(run, decisions)
