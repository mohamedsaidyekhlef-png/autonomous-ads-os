import pytest
from pydantic import ValidationError

from app.api.command_center import CommandResult, Recommendation
from app.main import app


def test_command_result_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        Recommendation(
            title="Scale campaign",
            action_type="adjust_budget",
            rationale="Campaign performance supports controlled scaling.",
            expected_impact="More profitable conversions",
            risk="medium",
            confidence=1.5,
            measurement="Review ROAS after seven days.",
        )


def test_command_center_routes_are_registered() -> None:
    paths = app.openapi()["paths"]

    assert "/v1/command/runs" in paths
    assert "/v1/command/runs/{run_id}" in paths


def test_command_result_requires_recommendations() -> None:
    with pytest.raises(ValidationError):
        CommandResult(
            executive_summary="A sufficiently detailed summary.",
            interpretation="Improve account performance.",
            verified_observations=[],
            assumptions=[],
            missing_information=[],
            diagnosis=[],
            recommendations=[],
            warnings=[],
            next_review_minutes=60,
        )
