from functools import partial
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from app.agents.expert_review.nodes import (
    calculate_metrics_node,
    finalize_node,
    human_review_node,
    synthesize_report_node,
    validate_evidence_node,
    validate_report_node,
)
from app.agents.expert_review.specialists import (
    SpecialistRunner,
    deterministic_specialist_runner,
)
from app.agents.expert_review.state import ExpertReviewState


def route_after_evidence(
    state: ExpertReviewState,
) -> Literal["continue", "stop"]:
    return "continue" if state["validation"].passed else "stop"


def route_after_report(
    state: ExpertReviewState,
) -> Literal["review", "stop"]:
    return "review" if state["validation"].passed else "stop"


def run_specialist(
    state: ExpertReviewState,
    *,
    agent_id: str,
    runner: SpecialistRunner,
) -> dict[str, object]:
    return runner(state, agent_id)


def build_expert_review_graph(
    *,
    checkpointer: Any = None,
    specialist_runner: SpecialistRunner | None = None,
):
    runner = (
        specialist_runner
        if specialist_runner is not None
        else deterministic_specialist_runner
    )

    workflow = StateGraph(ExpertReviewState)

    workflow.add_node(
        "validate_evidence",
        validate_evidence_node,
    )
    workflow.add_node(
        "calculate_metrics",
        calculate_metrics_node,
    )

    specialist_ids = (
        "measurement_auditor",
        "budget_controller",
        "chief_strategy",
        "risk_controller",
    )

    for specialist_id in specialist_ids:
        workflow.add_node(
            specialist_id,
            partial(
                run_specialist,
                agent_id=specialist_id,
                runner=runner,
            ),
        )

    workflow.add_node(
        "synthesize_report",
        synthesize_report_node,
    )
    workflow.add_node(
        "validate_report",
        validate_report_node,
    )
    workflow.add_node(
        "human_review",
        human_review_node,
    )
    workflow.add_node(
        "finalize",
        finalize_node,
    )

    workflow.add_edge(START, "validate_evidence")

    workflow.add_conditional_edges(
        "validate_evidence",
        route_after_evidence,
        {
            "continue": "calculate_metrics",
            "stop": END,
        },
    )

    for specialist_id in specialist_ids:
        workflow.add_edge(
            "calculate_metrics",
            specialist_id,
        )

    workflow.add_edge(
        list(specialist_ids),
        "synthesize_report",
    )
    workflow.add_edge(
        "synthesize_report",
        "validate_report",
    )

    workflow.add_conditional_edges(
        "validate_report",
        route_after_report,
        {
            "review": "human_review",
            "stop": END,
        },
    )

    workflow.add_edge("human_review", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile(
        checkpointer=checkpointer,
    )


def build_live_expert_review_graph(
    *,
    checkpointer: Any,
):
    from app.agents.expert_review.groq_runner import (
        GroqSpecialistRunner,
    )

    return build_expert_review_graph(
        checkpointer=checkpointer,
        specialist_runner=GroqSpecialistRunner(),
    )
