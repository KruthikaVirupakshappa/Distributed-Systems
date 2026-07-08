from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class GraphState(TypedDict, total=False):
    property_address: str
    property_details: Dict[str, Any]
    simulation_scenario: Optional[str]
    research_data: Dict[str, Any]
    valuation_data: Dict[str, Any]
    final_report: str
    interaction_log: List[str]
    trace: List[Dict[str, Any]]


def initialize_state(
    property_address: str,
    property_details: Dict[str, Any],
    simulation_scenario: Optional[str] = None,
) -> GraphState:
    return GraphState(
        property_address=property_address,
        property_details=property_details,
        simulation_scenario=simulation_scenario,
        interaction_log=[],
        trace=[],
    )

