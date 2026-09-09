import pytest
from pydantic import ValidationError

from app.agents.kernel.schemas import (
    ActionDisposition,
    AgentRisk,
    ProposedAction,
)
from app.agents.prompting import build_system_prompt
from app.agents.registry import (
    AGENT_REGISTRY,
    get_agent_profile,
)


def test_all_required_specialists_exist() -> None:
    required = {
        "chief_strategy",
        "measurement_auditor",
        "attribution_scientist",
        "google_search",
        "google_pmax",
        "meta_ads",
        "tiktok_ads",
        "budget_controller",
        "creative_research",
        "creative_director",
        "copywriter",
        "experiment_scientist",
        "compliance",
        "risk_controller",
        "cro_specialist",
        "reporting",
    }

    assert required.issubset(AGENT_REGISTRY)


def test_agent_prompt_contains_governance() -> None:
    profile = get_agent_profile("google_search")
    prompt = build_system_prompt(profile)

    assert "Google Search Specialist" in prompt
    assert "Never invent metrics" in prompt
    assert "deterministic policy engine" in prompt
    assert "negative-keyword" in prompt.lower()


def test_action_confidence_is_bounded() -> None:
    with pytest.raises(ValidationError):
        ProposedAction(
            disposition=ActionDisposition.PROPOSE,
            action_type="increase_budget",
            platform="google",
            account_id="account-1",
            target_type="campaign",
            target_id="campaign-1",
            parameters={"increase_percent": 10},
            rationale="Campaign has verified profitable marginal returns.",
            expected_effect="Increase qualified conversion volume.",
            reversible=True,
            rollback_condition="CPA exceeds the authorized threshold.",
            confidence=1.5,
            risk=AgentRisk.MEDIUM,
        )


def test_unknown_agent_is_rejected() -> None:
    with pytest.raises(ValueError):
        get_agent_profile("imaginary_agent")
