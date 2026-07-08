from __future__ import annotations

from langgraph.graph import StateGraph, END

from state import AgentState
from nodes import planner_node, reviewer_node, supervisor_node
from router import router_logic


def build_workflow():
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("reviewer", reviewer_node)

    workflow.set_entry_point("supervisor")

    # Supervisor decides what to do next
    workflow.add_conditional_edges(
        "supervisor",
        router_logic,
        {
            "run_planning": "planner",
            "run_review": "reviewer",
            "END": END,
        },
    )

    # Planner always goes to supervisor after completion
    workflow.add_edge("planner", "supervisor")

    # Reviewer always goes to supervisor after completion
    workflow.add_edge("reviewer", "supervisor")

    return workflow.compile()
