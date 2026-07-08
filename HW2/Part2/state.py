from __future__ import annotations

from typing import Any, Dict, TypedDict


class AgentState(TypedDict, total=False):
    title: str
    content: str
    email: str
    strict: bool
    task: str
    llm: Any
    planner_proposal: Dict[str, Any]
    reviewer_feedback: Dict[str, Any]
    reviewer_has_issues: bool
    turn_count: int
    interaction_log: list
    trace: list


def initialize_state(
    title: str,
    content: str,
    email: str,
    strict: bool,
    task: str,
    llm: Any = None,
) -> AgentState:
    return AgentState(
        title=title,
        content=content,
        email=email,
        strict=strict,
        task=task,
        llm=llm,
        planner_proposal={},
        reviewer_feedback={},
        turn_count=0,
        interaction_log=[],
        trace=[],
    )
