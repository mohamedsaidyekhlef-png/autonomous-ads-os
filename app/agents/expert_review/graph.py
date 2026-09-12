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
    budget_controller,
    campaign_strategist,
    measurement_auditor,
    risk_controller,
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


def build_expert_review_graph(
    *,
    checkpointer: Any = None,
):
    workflow = StateGraph(ExpertReviewState)

    workflow.add_node(
        "validate_evidence",
        validate_evidence_node,
    )
    workflow.add_node(
        "calculate_metrics",
        calculate_metrics_node,
    )
    workflow.add_node(
        "measurement_auditor",
        measurement_auditor,
    )
    workflow.add_node(
        "budget_controller",
        budget_controller,
    )
    workflow.add_node(
        "campaign_strategist",
        campaign_strategist,
    )
    workflow.add_node(
        "risk_controller",
        risk_controller,
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

    for specialist in (
        "measurement_auditor",
        "budget_controller",
        "campaign_strategist",
        "risk_controller",
    ):
        workflow.add_edge(
            "calculate_metrics",
            specialist,
        )

    workflow.add_edge(
        [
            "measurement_auditor",
            "budget_controller",
            "campaign_strategist",
            "risk_controller",
        ],
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
