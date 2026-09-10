import json
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.agents.registry import get_agent_profile
from app.core.settings import get_settings
from app.database.models import (
    AgentDecisionRecord,
    AgentRun,
    CampaignRecord,
    Organization,
)
from app.database.session import SessionLocal

router = APIRouter(prefix="/v1/command", tags=["Agent Command Center"])

DEFAULT_AGENTS = [
    "chief_strategy",
    "measurement_auditor",
    "budget_controller",
    "risk_controller",
]

SYSTEM_PROMPT = """
You are the Chief Strategy Brain of Autonomous Ads OS.

You coordinate a senior advertising team responsible for strategy,
measurement, budgeting, experimentation, creative direction, compliance,
risk protection and platform-specific execution.

OPERATING PRINCIPLES

1. Never invent performance data, conversion data, product facts or customer
   facts.
2. Distinguish verified evidence from assumptions.
3. Never claim that a platform mutation occurred unless an execution adapter
   returned a verified result.
4. The current environment is shadow mode. You may analyze, diagnose, create
   drafts and recommend actions, but you must not claim to have spent money.
5. Protect capital. Recommend reversible actions and explicit stop-loss rules.
6. Do not optimize clicks when the stated objective is profit, revenue,
   purchases, qualified leads or customer lifetime value.
7. If tracking data is missing, say so and reduce confidence.
8. Every recommendation needs rationale, expected impact, risk and confidence.
9. Do not recommend scaling without reliable conversion evidence.
10. Return only JSON matching the supplied schema.

DECISION PROCESS

- Interpret the customer's command.
- Review verified business and campaign context.
- Identify missing information.
- Diagnose the current situation.
- Generate multiple reasonable actions.
- Reject actions that violate budget, measurement or evidence constraints.
- Select the safest high-value actions.
- Define how each action should be measured.
- Set an appropriate next review interval.

You are not a generic assistant. You are an evidence-driven advertising
operations team working under deterministic policy controls.
""".strip()


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
    recommendations: list[Recommendation] = Field(
        min_length=1,
        max_length=8,
    )
    warnings: list[str]
    next_review_minutes: int = Field(ge=15, le=10080)


def development_organization() -> Organization:
    settings = get_settings()

    if settings.app_env != "development":
        raise HTTPException(
            status_code=401,
            detail="Authenticated organization context is required.",
        )

    with SessionLocal() as database:
        organization = database.scalars(
            select(Organization)
            .where(Organization.status == "active")
            .order_by(Organization.created_at)
            .limit(1)
        ).first()

        if organization is None:
            raise HTTPException(
                status_code=409,
                detail="No active organization exists.",
            )

        database.expunge(organization)
        return organization


def validate_agents(agent_ids: list[str]) -> list[dict[str, Any]]:
    if not agent_ids:
        raise HTTPException(
            status_code=422,
            detail="Select at least one agent.",
        )

    profiles: list[dict[str, Any]] = []

    for agent_id in dict.fromkeys(agent_ids):
        try:
            profile = get_agent_profile(agent_id)
        except KeyError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown agent: {agent_id}",
            ) from exc

        profiles.append(profile.model_dump(mode="json"))

    return profiles


def command_context(
    organization: Organization,
    profiles: list[dict[str, Any]],
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
                "daily_spend_cap_minor": (organization.daily_spend_cap_minor),
                "monthly_spend_cap_minor": (organization.monthly_spend_cap_minor),
                "automation_enabled": organization.automation_enabled,
            },
            "agents": profiles,
            "campaigns": [
                {
                    "id": str(campaign.id),
                    "name": campaign.name,
                    "platform": campaign.platform,
                    "status": campaign.status,
                    "objective": campaign.objective,
                    "daily_budget_minor": campaign.daily_budget_minor,
                    "currency": campaign.currency,
                    "metrics": campaign.metrics,
                }
                for campaign in campaigns
            ],
            "data_quality": {
                "source": "local_database",
                "live_platform_data": False,
                "tracking_verified": False,
                "execution_mode": "shadow",
            },
        }


async def run_qwen(
    command: str,
    context: dict[str, Any],
) -> CommandResult:
    settings = get_settings()

    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "think": False,
        "format": CommandResult.model_json_schema(),
        "options": {
            "temperature": 0.1,
        },
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "customer_command": command,
                        "verified_context": context,
                        "required_behavior": {
                            "mode": "shadow",
                            "do_not_invent_metrics": True,
                            "do_not_claim_execution": True,
                        },
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            response_data = response.json()

        content = response_data["message"]["content"]
        return CommandResult.model_validate_json(content)
    except (
        httpx.HTTPError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=502,
            detail=("Qwen could not produce a valid structured agent decision."),
        ) from exc


def create_run(
    organization_id: uuid.UUID,
    request: CommandRequest,
) -> AgentRun:
    try:
        with SessionLocal() as database:
            run = AgentRun(
                organization_id=organization_id,
                status="running",
                mode=request.mode,
                trigger_source="command_center",
                objective=request.command,
                selected_agents=request.selected_agents,
                started_at=datetime.now(UTC),
            )
            database.add(run)
            database.commit()
            database.refresh(run)
            database.expunge(run)
            return run
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not create the agent run.",
        ) from exc


def fail_run(run_id: uuid.UUID, message: str) -> None:
    try:
        with SessionLocal() as database:
            run = database.get(AgentRun, run_id)

            if run is not None:
                run.status = "failed"
                run.error_message = message
                run.completed_at = datetime.now(UTC)
                database.commit()
    except SQLAlchemyError:
        return


def persist_result(
    organization: Organization,
    run: AgentRun,
    request: CommandRequest,
    result: CommandResult,
) -> list[str]:
    draft_ids: list[str] = []

    try:
        with SessionLocal() as database:
            stored_run = database.get(AgentRun, run.id)

            if stored_run is None:
                raise HTTPException(
                    status_code=404,
                    detail="Agent run disappeared before completion.",
                )

            for recommendation in result.recommendations:
                decision = AgentDecisionRecord(
                    organization_id=organization.id,
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
                database.add(decision)

                should_create_draft = (
                    request.create_campaign_draft
                    and recommendation.action_type == "create_campaign"
                )

                if should_create_draft:
                    campaign = CampaignRecord(
                        organization_id=organization.id,
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
                        },
                        metrics={},
                    )
                    database.add(campaign)
                    database.flush()
                    draft_ids.append(str(campaign.id))

            stored_run.status = "completed"
            stored_run.result_summary = result.executive_summary
            stored_run.completed_at = datetime.now(UTC)
            database.commit()

        return draft_ids
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Agent result could not be persisted.",
        ) from exc


@router.post("/runs", status_code=201)
async def create_command_run(
    request: CommandRequest,
) -> dict[str, Any]:
    organization = development_organization()
    profiles = validate_agents(request.selected_agents)
    context = command_context(organization, profiles)
    run = create_run(organization.id, request)

    try:
        result = await run_qwen(request.command, context)
        draft_ids = persist_result(
            organization,
            run,
            request,
            result,
        )
    except HTTPException as exc:
        fail_run(run.id, str(exc.detail))
        raise

    return {
        "run_id": str(run.id),
        "status": "completed",
        "mode": request.mode,
        "result": result.model_dump(mode="json"),
        "campaign_draft_ids": draft_ids,
    }


@router.get("/runs")
def list_command_runs() -> list[dict[str, Any]]:
    organization = development_organization()

    with SessionLocal() as database:
        runs = database.scalars(
            select(AgentRun)
            .where(AgentRun.organization_id == organization.id)
            .order_by(AgentRun.created_at.desc())
            .limit(50)
        ).all()

        return [
            {
                "id": str(run.id),
                "status": run.status,
                "mode": run.mode,
                "objective": run.objective,
                "selected_agents": run.selected_agents,
                "result_summary": run.result_summary,
                "error_message": run.error_message,
                "created_at": run.created_at.isoformat(),
                "completed_at": (
                    run.completed_at.isoformat() if run.completed_at else None
                ),
            }
            for run in runs
        ]


@router.get("/runs/{run_id}")
def get_command_run(run_id: uuid.UUID) -> dict[str, Any]:
    organization = development_organization()

    with SessionLocal() as database:
        run = database.get(AgentRun, run_id)

        if run is None or run.organization_id != organization.id:
            raise HTTPException(
                status_code=404,
                detail="Agent run was not found.",
            )

        decisions = database.scalars(
            select(AgentDecisionRecord)
            .where(AgentDecisionRecord.agent_run_id == run.id)
            .order_by(AgentDecisionRecord.created_at)
        ).all()

        return {
            "id": str(run.id),
            "status": run.status,
            "mode": run.mode,
            "objective": run.objective,
            "result_summary": run.result_summary,
            "error_message": run.error_message,
            "decisions": [
                {
                    "id": str(decision.id),
                    "agent_id": decision.agent_id,
                    "status": decision.status,
                    "rationale": decision.rationale,
                    "confidence": decision.confidence,
                    "risk": decision.risk,
                    "evidence": decision.evidence,
                    "proposed_actions": decision.proposed_actions,
                }
                for decision in decisions
            ],
        }
