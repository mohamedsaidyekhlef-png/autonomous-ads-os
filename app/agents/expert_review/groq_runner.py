import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.agents.expert_review.schemas import SpecialistAssessment
from app.agents.expert_review.state import ExpertReviewState
from app.agents.registry import get_agent_profile
from app.core.settings import get_settings


class ExpertModelUnavailable(RuntimeError):
    """The configured expert model cannot be used."""


def build_specialist_system_prompt(agent_id: str) -> str:
    profile = get_agent_profile(agent_id)

    responsibilities = "\n".join(f"- {item}" for item in profile.responsibilities)
    prohibited = "\n".join(f"- {item}" for item in profile.prohibited_behaviors)
    evaluation = "\n".join(f"- {item}" for item in profile.evaluation_criteria)

    return f"""
You are {profile.name}, a governed specialist inside Autonomous Ads OS.

MISSION
{profile.mission}

RESPONSIBILITIES
{responsibilities}

PROHIBITED BEHAVIOURS
{prohibited}

QUALITY CRITERIA
{evaluation}

MANDATORY EVIDENCE RULES
- Use only evidence supplied in the task package.
- Never invent metrics, settings, customers, campaigns, or outcomes.
- Every factual finding must cite valid evidence_ids.
- Every recommendation must cite valid evidence_ids.
- If evidence is missing, list it under missing_information.
- Label uncertainty honestly.
- Do not claim causation from correlation.
- Do not claim guaranteed performance.
- Do not provide hidden chain-of-thought.
- Return concise conclusions and evidence references only.

EXECUTION RULES
- Operate exclusively in Shadow Mode.
- Do not publish, pause, create, or edit campaigns.
- Do not change budgets, bids, audiences, or payment settings.
- Every recommendation requires human approval.
- Recommendations should be reversible whenever possible.

Return only the structured specialist assessment requested by the schema.
""".strip()


def build_specialist_task_payload(
    state: ExpertReviewState,
    agent_id: str,
) -> str:
    payload = {
        "agent_id": agent_id,
        "run_id": state["run_id"],
        "evidence": state["evidence"].model_dump(mode="json"),
        "calculated_metrics": [
            item.model_dump(mode="json")
            for item in state.get(
                "calculated_metrics",
                [],
            )
        ],
    }

    return (
        "Review this campaign evidence package. "
        "Cite only evidence IDs contained in the package.\n\n"
        + json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
    )


class GroqSpecialistRunner:
    def __init__(self, model: Any | None = None) -> None:
        self._model = model

    def _chat_model(self) -> Any:
        if self._model is not None:
            return self._model

        settings = get_settings()

        if not settings.groq_api_key:
            raise ExpertModelUnavailable("GROQ_API_KEY is not configured.")

        return ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0.1,
            timeout=settings.llm_timeout_seconds,
            max_retries=2,
            max_tokens=2500,
        )

    def __call__(
        self,
        state: ExpertReviewState,
        agent_id: str,
    ) -> dict[str, object]:
        profile = get_agent_profile(agent_id)
        chat_model = self._chat_model()

        structured_model = chat_model.with_structured_output(
            SpecialistAssessment,
            method="function_calling",
        )

        response = structured_model.invoke(
            [
                SystemMessage(content=build_specialist_system_prompt(agent_id)),
                HumanMessage(
                    content=build_specialist_task_payload(
                        state,
                        agent_id,
                    )
                ),
            ]
        )

        assessment = (
            response
            if isinstance(response, SpecialistAssessment)
            else SpecialistAssessment.model_validate(response)
        )

        assessment = assessment.model_copy(
            update={
                "agent_id": agent_id,
                "role_name": profile.name,
                "recommendations": [
                    item.model_copy(
                        update={
                            "requires_human_approval": True,
                        }
                    )
                    for item in assessment.recommendations
                ],
            }
        )

        return {
            "specialist_assessments": [assessment],
        }
