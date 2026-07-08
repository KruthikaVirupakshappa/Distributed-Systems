from __future__ import annotations

import os
import json
import time
from typing import Any, Dict, List

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage

from state import AgentState


def _get_model_default() -> ChatOllama:
    return ChatOllama(
        model="llama3.2:3b",
        temperature=0.5,
    )


def planner_node(state: AgentState) -> Dict[str, Any]:
    interaction_log = state.get("interaction_log", [])
    trace = state.get("trace", [])
    interaction_log.append("Planner: start")
    print("[Planner] Node activated")

    llm = _get_model_default()
    title = state.get("title", "")
    content = state.get("content", "")
    
    prompt = f"""You must respond with ONLY valid JSON. Nothing else.

    TEXT: {content}

        Create exactly:
        - 3 tags (1-3 words each, related to the content and title)
        - 1 summary (max 25 words)

        Your response must be valid JSON only:
        {{"tags": ["tag1", "tag2", "tag3"], "summary": "Summary here."}}"""

    try:
        t0 = time.time()
        msg = llm.invoke([HumanMessage(content=prompt)])
        t1 = time.time()
        content_response = getattr(msg, "content", "").strip()
        
        trace.append({
            "agent": "Planner",
            "type": "ai_message",
            "content": content_response,
            "metadata": {"latency_ms": int((t1 - t0) * 1000)},
            "ts": t1,
        })
        
        parsed = None

        try:
            parsed = json.loads(content_response)
        except Exception as err:
            print(f"[Planner] JSON parse error: {err}")

    except Exception as err:
        print(f"[Planner] ERROR: {err}")

    if parsed is None:
        parsed = {"tags": [], "summary": ""}

    interaction_log.append("Planner: complete")
    return {
        "planner_proposal": parsed,
        "reviewer_has_issues": None,
        "interaction_log": interaction_log,
        "trace": trace,
    }


def reviewer_node(state: AgentState) -> Dict[str, Any]:
    interaction_log = state.get("interaction_log", [])
    trace = state.get("trace", [])
    interaction_log.append("Reviewer: start")
    print("[Reviewer] Node activated")

    llm = _get_model_default()
    title = state.get("title", "")
    content = state.get("content", "")
    proposal = state.get("planner_proposal", {})
    
    tags = proposal.get("tags", [])
    summary = proposal.get("summary", "")

    prompt = f"""You must respond with ONLY valid JSON. Nothing else.

    TEXT: {content}

    CURRENT TAGS: {tags}
    CURRENT SUMMARY: {summary}

    Validate and return:
    - 3 tags (each 1-3 words)
    - Summary (1-2 sentences, max 25 words)

    Response must be valid JSON only:
    {{"tags": ["tag1", "tag2", "tag3"], "summary": "Summary sentence."}}"""

    try:
        t0 = time.time()
        msg = llm.invoke([HumanMessage(content=prompt)])
        t1 = time.time()
        content_response = getattr(msg, "content", "").strip()
        trace.append({
            "agent": "Reviewer",
            "type": "ai_message",
            "content": content_response,
            "metadata": {"latency_ms": int((t1 - t0) * 1000)},
            "ts": t1,
        })
        
        try:
            result = json.loads(content_response)
        except:
            print(f"Reviewer Could not extract JSON, using current values")
            result = {"tags": tags, "summary": summary, "review_notes": ["Failed to fetch review results"]}
       
    except Exception as err:
        print(f"[Reviewer] ERROR: {err}")
        result = {"tags": tags, "summary": summary, "review_notes": [str(err)]}

    interaction_log.append("Reviewer: complete")
    
    review_notes = []
    
    result_tags = result.get("tags", [])
    result_summary = result.get("summary", "")
    
    # Check tag count
    if len(result_tags) != 3:
        review_notes.append(f"Tags count is {len(result_tags)}, expected exactly 3")
    
    # Check summary word count
    summary_word_count = len(result_summary.split()) if result_summary else 0
    if summary_word_count > 25:
        review_notes.append(f"Summary has {summary_word_count} words, maximum is 25")
    if summary_word_count == 0:
        review_notes.append("Summary is empty")
    
    result["review_notes"] = review_notes
    
    # has issues if review_notes is not empty
    #reviewer_has_issues = bool(review_notes)
    # Force set to true to check the feedback loop
    reviewer_has_issues = True

    return {
        "reviewer_feedback": result,
        "reviewer_has_issues": reviewer_has_issues,
        "interaction_log": interaction_log,
        "trace": trace,
    }


def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """Increments turn counter.

    Returns updated `turn_count`.
    """
    turn = state.get("turn_count", 0) + 1
    return {"turn_count": turn}
