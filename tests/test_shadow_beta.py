import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import command_center
from app.api.command_center import (
    CommandRequest,
    CommandResult,
    Recommendation,
    process_run,
)
from app.core.auth import OrganizationContext, require_organization_context
from app.database.base import Base
from app.database.models import AgentRun, Organization


@pytest.fixture
def database(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(command_center, "SessionLocal", session_local)
    return session_local


def test_queue_response_is_idempotent_and_queued(database, monkeypatch) -> None:
    from app.main import app

    org = Organization(name="One", status="active")
    with database() as session:
        session.add(org)
        session.commit()
        session.refresh(org)
    app.dependency_overrides[require_organization_context] = lambda: (
        OrganizationContext(org.id, None, "owner")
    )
    queued: list[uuid.UUID] = []
    monkeypatch.setattr(command_center, "enqueue_run", queued.append)
    try:
        response = TestClient(app).post(
            "/v1/command/runs",
            headers={"Idempotency-Key": "same"},
            json={"command": "Create a protected campaign draft."},
        )
        again = TestClient(app).post(
            "/v1/command/runs",
            headers={"Idempotency-Key": "same"},
            json={"command": "Create a protected campaign draft."},
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    assert response.json()["status_url"].endswith(response.json()["run_id"])
    assert again.json()["run_id"] == response.json()["run_id"]
    assert len(queued) == 1


def test_worker_completes_once_and_persists_result(database, monkeypatch) -> None:
    org = Organization(name="One", status="active")
    with database() as session:
        session.add(org)
        session.commit()
        session.refresh(org)
        run = AgentRun(
            organization_id=org.id,
            status="queued",
            mode="shadow",
            objective="Analyze safely",
            selected_agents=["chief_strategy"],
            request_data=CommandRequest(
                command="Analyze safely", selected_agents=["chief_strategy"]
            ).model_dump(mode="json"),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        run_id = run.id

    async def result(*_args, **_kwargs):
        return CommandResult(
            executive_summary="A safe structured shadow plan.",
            interpretation="Inspect performance safely.",
            verified_observations=[],
            assumptions=[],
            missing_information=[],
            diagnosis=["No live data is available."],
            recommendations=[
                Recommendation(
                    title="Request tracking access",
                    action_type="request_information",
                    rationale="Tracking evidence is missing and needs validation.",
                    expected_impact="Safer recommendations",
                    risk="low",
                    confidence=0.8,
                    measurement="Review tracking status tomorrow.",
                )
            ],
            warnings=[],
            next_review_minutes=60,
        )

    monkeypatch.setattr(command_center, "run_llm", result)
    process_run(run_id)
    process_run(run_id)
    with database() as session:
        stored = session.get(AgentRun, run_id)
        assert stored.status == "completed"
        assert stored.result_data is not None
        assert session.query(command_center.AgentDecisionRecord).count() == 1


def test_run_cannot_cross_tenants(database) -> None:
    first, second = (
        Organization(name="One", status="active"),
        Organization(name="Two", status="active"),
    )
    with database() as session:
        session.add_all([first, second])
        session.commit()
        session.refresh(first)
        session.refresh(second)
        run = AgentRun(
            organization_id=first.id,
            status="queued",
            mode="shadow",
            objective="safe",
            selected_agents=[],
            request_data={},
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        assert run.organization_id != second.id
