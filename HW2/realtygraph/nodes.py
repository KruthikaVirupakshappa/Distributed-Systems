from __future__ import annotations

import os
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
import json
import time

from .state import GraphState
from .tools import get_tavily_tool


def _get_model_default() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def market_researcher_node(state: GraphState) -> Dict[str, Any]:
    interaction_log = state.get("interaction_log", [])
    trace = state.get("trace", [])
    print("[MarketResearcher] Node activated")
    interaction_log.append("MarketResearcher: start")

    llm = ChatOpenAI(model=_get_model_default(), temperature=float(os.getenv("OPENAI_TEMPERATURE", "0")))
    tavily = get_tavily_tool()
    model_with_tools = llm.bind_tools([tavily])

    system_text = (
        "You are MarketResearcher, a real estate market data gatherer. "
        "Given a property location, call tools as needed and produce a concise JSON object with: "
        "mortgage_rates, local_news, market_trends, comparables (list). Return only JSON."
    )

    address = state.get("property_address", "")
    messages: List[Any] = [
        SystemMessage(content=system_text),
        HumanMessage(content=f"Property location: {address}"),
    ]

    research_payload: Dict[str, Any] = {}
    try:
        # Simple tool-execution loop (max 3 rounds)
        for _ in range(3):
            t0 = time.time()
            ai: AIMessage = model_with_tools.invoke(messages)
            t1 = time.time()
            meta_raw = getattr(ai, "response_metadata", {}) or {}
            usage = meta_raw.get("token_usage") or meta_raw.get("usage") or {}
            meta = {
                **meta_raw,
                "input_tokens": usage.get("input_tokens") or usage.get("prompt_tokens") or meta_raw.get("input_tokens") or meta_raw.get("prompt_tokens"),
                "output_tokens": usage.get("output_tokens") or usage.get("completion_tokens") or meta_raw.get("output_tokens") or meta_raw.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
                "latency_ms": int((t1 - t0) * 1000),
            }
            trace.append({
                "agent": "MarketResearcher",
                "type": "ai_message",
                "content": ai.content,
                "metadata": meta,
                "ts": t1,
            })
            if getattr(ai, "tool_calls", None):
                messages.append(ai)
                for tool_call in ai.tool_calls:
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("args", {})
                    query = tool_args.get("query") or tool_args.get("input") or "real estate market trends"
                    print(f"[MarketResearcher] Executing tool: {tool_name} query={query!r}")
                    try:
                        s0 = time.time()
                        tool_result = tavily.invoke(query)
                        s1 = time.time()
                    except Exception as tool_err:
                        tool_result = {"error": str(tool_err)}
                        s1 = time.time()
                    trace.append({
                        "agent": "MarketResearcher",
                        "type": "tool_result",
                        "tool": tool_name,
                        "args": {"query": query},
                        "result": tool_result,
                        "metadata": {"latency_ms": int((s1 - s0) * 1000)},
                        "ts": s1,
                    })
                    messages.append(
                        ToolMessage(
                            content=json.dumps(tool_result),
                            tool_call_id=tool_call.get("id", ""),
                        )
                    )
                continue
            final_text = ai.content or "{}"
            try:
                research_payload = json.loads(final_text)
            except Exception:
                research_payload = {"raw": final_text}
            break
    except Exception as err:
        print(f"[MarketResearcher] ERROR: {err}")
        research_payload = {"error": str(err)}

    interaction_log.append("MarketResearcher: complete")
    return {
        "research_data": research_payload,
        "interaction_log": interaction_log,
        "trace": trace,
    }


def valuation_analyst_node(state: GraphState) -> Dict[str, Any]:
    interaction_log = state.get("interaction_log", [])
    trace = state.get("trace", [])
    print("[ValuationAnalyst] Node activated")
    interaction_log.append("ValuationAnalyst: start")

    llm = ChatOpenAI(model=_get_model_default(), temperature=float(os.getenv("OPENAI_TEMPERATURE", "0")))
    parser = JsonOutputParser()
    system = (
        "You are ValuationAnalyst, a quantitative analyst. Using research_data and property_details, "
        "estimate a base_valuation (USD), confidence_score (0-100), valuation_factors (list of strings), and scenario_analysis if provided. "
        "Return a compact JSON object with keys: base_valuation, confidence_score, valuation_factors, scenario_analysis."
    )
    human = (
        "Property details: {details}\n"
        "Research data: {research}\n"
        "Scenario (optional): {scenario}\n"
        "Return only JSON."
    )
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])
    chain = prompt | llm
    try:
        t0 = time.time()
        text = chain.invoke(
            {
                "details": state.get("property_details", {}),
                "research": state.get("research_data", {}),
                "scenario": state.get("simulation_scenario", ""),
            }
        )
        t1 = time.time()
        # chain returns an AIMessage; extract content
        content = getattr(text, "content", "{}")
        meta_raw = getattr(text, "response_metadata", {}) or {}
        usage = meta_raw.get("token_usage") or meta_raw.get("usage") or {}
        meta = {
            **meta_raw,
            "input_tokens": usage.get("input_tokens") or usage.get("prompt_tokens") or meta_raw.get("input_tokens") or meta_raw.get("prompt_tokens"),
            "output_tokens": usage.get("output_tokens") or usage.get("completion_tokens") or meta_raw.get("output_tokens") or meta_raw.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "latency_ms": int((t1 - t0) * 1000),
        }
        trace.append({
            "agent": "ValuationAnalyst",
            "type": "ai_message",
            "content": content,
            "metadata": meta,
            "ts": t1,
        })
        try:
            result = json.loads(content)
        except Exception:
            # Fallback: try strict parser
            try:
                result = parser.parse(content)
            except Exception:
                result = {"raw": content}
    except Exception as err:
        print(f"[ValuationAnalyst] ERROR: {err}")
        result = {"error": str(err)}

    interaction_log.append("ValuationAnalyst: complete")
    return {
        "valuation_data": result,
        "interaction_log": interaction_log,
        "trace": trace,
    }


def client_presenter_node(state: GraphState) -> Dict[str, Any]:
    interaction_log = state.get("interaction_log", [])
    trace = state.get("trace", [])
    print("[ClientPresenter] Node activated")
    interaction_log.append("ClientPresenter: start")

    llm = ChatOpenAI(model=_get_model_default(), temperature=0)
    system = (
        "You are ClientPresenter, a senior real estate advisor. Given valuation_data, write a polished Markdown report "
        "with sections: Base Valuation, Key Market Factors, Scenario Analysis."
    )
    human = (
        "Valuation data: {valuation}\n"
        "Write a clear, client-friendly Markdown report."
    )
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])
    try:
        t0 = time.time()
        msg = (prompt | llm).invoke({"valuation": state.get("valuation_data", {})})
        t1 = time.time()
        report_md = getattr(msg, "content", "")
        meta_raw = getattr(msg, "response_metadata", {}) or {}
        usage = meta_raw.get("token_usage") or meta_raw.get("usage") or {}
        meta = {
            **meta_raw,
            "input_tokens": usage.get("input_tokens") or usage.get("prompt_tokens") or meta_raw.get("input_tokens") or meta_raw.get("prompt_tokens"),
            "output_tokens": usage.get("output_tokens") or usage.get("completion_tokens") or meta_raw.get("output_tokens") or meta_raw.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "latency_ms": int((t1 - t0) * 1000),
        }
        trace.append({
            "agent": "ClientPresenter",
            "type": "render",
            "content": report_md,
            "metadata": meta,
            "ts": t1,
        })
    except Exception as err:
        print(f"[ClientPresenter] ERROR: {err}")
        report_md = "# Report\nAn error occurred while generating the report."

    interaction_log.append("ClientPresenter: complete")
    return {
        "final_report": report_md,
        "interaction_log": interaction_log,
        "trace": trace,
    }

