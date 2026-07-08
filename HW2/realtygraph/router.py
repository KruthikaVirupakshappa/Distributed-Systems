from __future__ import annotations

from typing import Literal

from .state import GraphState


def router_logic(state: GraphState) -> Literal["run_research", "run_analysis", "generate_report", "END"]:
    if not state.get("research_data"):
        return "run_research"
    if not state.get("valuation_data"):
        return "run_analysis"
    if not state.get("final_report"):
        return "generate_report"
    return "END"

