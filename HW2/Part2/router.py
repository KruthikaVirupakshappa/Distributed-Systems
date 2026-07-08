from __future__ import annotations

from typing import Literal

from state import AgentState


def router_logic(state: AgentState) -> Literal["run_planning", "run_review", "END"]:
    turn = state.get("turn_count", 0)
    has_proposal = bool(state.get("planner_proposal"))
    has_reviewer_issues_key = "reviewer_has_issues" in state
    reviewer_has_issues = state.get("reviewer_has_issues", None) if has_reviewer_issues_key else None

    print(f"[Router] turn={turn}, has_proposal={has_proposal}, reviewer_has_issues={reviewer_has_issues}")

    if turn > 6:
        print(f"[Router] -> END (turn > 6)")
        return "END"

    if not has_proposal:
        print(f"[Router] -> run_planning (no proposal)")
        return "run_planning"

    # If reviewer_has_issues is True, go back to planning
    if reviewer_has_issues is True:
        print(f"[Router] -> run_planning (reviewer has issues)")
        return "run_planning"

    # If reviewer_has_issues is False, end workflow
    if reviewer_has_issues is False:
        print(f"[Router] -> END (reviewer has no issues)")
        return "END"

    # For None, run the review again.
    print(f"[Router] -> run_review (has proposal, review needed)")
    return "run_review"
