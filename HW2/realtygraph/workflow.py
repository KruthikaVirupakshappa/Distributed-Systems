from __future__ import annotations

from langgraph.graph import StateGraph, END

from .state import GraphState
from .nodes import market_researcher_node, valuation_analyst_node, client_presenter_node
from .router import router_logic


def build_workflow():
    workflow = StateGraph(GraphState)

    workflow.add_node("market_researcher", market_researcher_node)
    workflow.add_node("valuation_analyst", valuation_analyst_node)
    workflow.add_node("client_presenter", client_presenter_node)

    workflow.set_entry_point("market_researcher")

    workflow.add_conditional_edges(
        "market_researcher",
        router_logic,
        {
            "run_research": "market_researcher",
            "run_analysis": "valuation_analyst",
            "generate_report": "client_presenter",
            "END": END,
        },
    )

    workflow.add_conditional_edges(
        "valuation_analyst",
        router_logic,
        {
            "run_research": "market_researcher",
            "run_analysis": "valuation_analyst",
            "generate_report": "client_presenter",
            "END": END,
        },
    )

    workflow.add_conditional_edges(
        "client_presenter",
        router_logic,
        {
            "END": END,
            "run_research": "market_researcher",
            "run_analysis": "valuation_analyst",
            "generate_report": "client_presenter",
        },
    )

    return workflow.compile()

