"""
Single-Agent ReAct + MRKL Bike-Share Pass Optimizer
Uses Groq (Llama 3.3 70B) via OpenAI-compatible API.
"""
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from typing import AsyncGenerator

import duckdb
from dotenv import load_dotenv
from openai import AsyncOpenAI

from tools import csv_sql, policy_retriever, calculator

load_dotenv()
client = AsyncOpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

# ─── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a bike-share financial advisor. Analyze a rider's Citi Bike trip CSV and recommend Monthly Membership or Pay Per Ride/Minute.

Tools available:
- csv_sql: run SQL on the DuckDB table named `trips`
- policy_retriever: fetch pricing page snippets
- calculator: evaluate arithmetic (digits and + - * / ( ) . only)

Steps to follow in order:
1. Run `SELECT * FROM trips LIMIT 3` to discover column names.
2. Run one query: COUNT(*) AS total_rides, AVG(DATEDIFF('minute', started_at, ended_at)) AS avg_duration_min, eBike percentage.
3. Weekly breakdown: WITH w AS (SELECT *, NTILE(4) OVER (ORDER BY started_at) AS week FROM trips) SELECT week, COUNT(*) AS rides, AVG(DATEDIFF('minute', started_at, ended_at)) AS avg_duration_min FROM w GROUP BY week ORDER BY week.
4. Fetch pricing policy to get unlock fee, monthly membership cost, included minutes, overage rates.
5. calculator: pay_per_use_total = total_rides * unlock_fee
6. calculator: break_even = membership_cost / unlock_fee
7. calculator: savings = pay_per_use_total - membership_cost

IMPORTANT rules:
- total_rides is the COUNT of rows, NOT avg_duration_min. These are different numbers.
- Monthly membership fee is a flat monthly cost. Do NOT multiply it by days.
- Use the exact total_rides from the CSV row count in all calculations.

Final answer must use EXACTLY these section headers:

**DECISION:** Buy Monthly Membership  OR  Pay Per Ride/Minute

**JUSTIFICATION:**
3-6 sentences citing specific policy prices.

**COST BREAKDOWN:**
- Total rides analysed: N
- Pay-per-use total: $X.XX
- Monthly membership: $X.XX
- Break-even rides: N rides/month (actual: N)
- Savings: $X.XX with [recommended plan]

**WEEKLY TABLE:**
| Week | Rides | Avg Duration (min) | eBike % | Spend (pay-per-use $) |
|------|-------|--------------------|---------|----------------------|

**ASSUMPTIONS & CAVEATS:**
- bullet list

**CITATIONS:**
- "[exact quote]" — source: <URL>, captured: <date>
"""

# ─── Tool schemas (OpenAI format) ──────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "csv_sql",
            "description": "Run a read-only SQL SELECT query on the uploaded Citi Bike trip data. The DuckDB table is named 'trips'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "A SQL SELECT or WITH...SELECT query against the 'trips' table."},
                },
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "policy_retriever",
            "description": "Fetch the official pricing page and return quotable snippets about membership price, unlock fees, included minutes, and per-minute surcharges.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url":   {"type": "string",  "description": "URL of the pricing page."},
                    "query": {"type": "string",  "description": "What pricing info to extract."},
                    "k":     {"type": "integer", "description": "Max snippets to return (default 8)."},
                },
                "required": ["url", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a safe arithmetic expression. Only digits and + - * / ( ) . are allowed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Arithmetic expression e.g. '7 * 4.99'."},
                    "units":      {"type": "string", "description": "Optional label e.g. 'USD'."},
                },
                "required": ["expression"],
            },
        },
    },
]

MAX_STEPS = 20


# ─── Tool dispatcher ───────────────────────────────────────────────────────────

def _run_tool(name: str, args: dict, db_conn: duckdb.DuckDBPyConnection) -> dict:
    if name == "csv_sql":
        return csv_sql(args.get("sql", ""), db_conn)
    if name == "policy_retriever":
        return policy_retriever(args.get("url", ""), args.get("query", ""), args.get("k", 8))
    if name == "calculator":
        return calculator(args.get("expression", ""), args.get("units"))
    return {"success": False, "error": f"Unknown tool: {name}"}


# ─── Agent loop ────────────────────────────────────────────────────────────────

async def run_react_agent(
    pricing_url: str,
    db_conn: duckdb.DuckDBPyConnection,
    model: str = "llama-3.3-70b-versatile",
    total_rides: int | None = None,
) -> AsyncGenerator[dict, None]:
    capture_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    ride_note = (
        f"\nThe uploaded CSV contains exactly {total_rides} rides. Use {total_rides} as total_rides in all calculations.\n"
        if total_rides is not None else ""
    )

    initial_text = (
        f"Analyse the uploaded Citi Bike trip CSV and recommend the best pricing plan.\n"
        f"Official pricing URL: {pricing_url}\n"
        f"Pricing page captured: {capture_date}"
        f"{ride_note}"
    )

    # Conversation history (OpenAI format)
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": initial_text},
    ]

    step_count = 0
    start_time = time.time()
    stop_reason = "max_steps"
    step_logs: list[dict] = []
    collected_citations: list[dict] = []
    calc_results: list[dict] = []

    while step_count < MAX_STEPS:
        step_count += 1

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.0,
            )
        except Exception as exc:
            yield {"type": "error", "content": str(exc), "step": step_count}
            stop_reason = "llm_error"
            break

        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # Add assistant message to history (only include fields Groq accepts)
        msg_dict: dict = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            msg_dict["tool_calls"] = [tc.model_dump() for tc in msg.tool_calls]
        messages.append(msg_dict)

        # Emit any text content as a thought
        if msg.content:
            yield {"type": "thought", "step": step_count, "content": msg.content}

        # Process tool calls
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_args = json.loads(tc.function.arguments)
                except Exception:
                    tool_args = {}
                raw_args = json.dumps(tool_args, sort_keys=True)
                args_hash = hashlib.md5(raw_args.encode()).hexdigest()[:8]

                yield {
                    "type": "action",
                    "step": step_count,
                    "tool": tool_name,
                    "args": tool_args,
                    "args_hash": args_hash,
                }

                t0 = time.time()
                try:
                    result = _run_tool(tool_name, tool_args, db_conn)
                except Exception as exc:
                    result = {"success": False, "error": str(exc)}
                latency_ms = round((time.time() - t0) * 1000, 1)

                step_logs.append({
                    "step": step_count,
                    "tool": tool_name,
                    "args_hash": args_hash,
                    "latency_ms": latency_ms,
                    "success": result.get("success", False),
                    "stop_reason": "tool_use",
                })

                obs_data = result.get("data", result)
                obs_str = json.dumps(obs_data)
                if len(obs_str) > 4000:
                    if isinstance(obs_data, dict) and "rows" in obs_data:
                        obs_data = {**obs_data, "rows": obs_data["rows"][:20], "_note": "rows truncated"}
                        obs_str = json.dumps(obs_data)
                    else:
                        obs_str = obs_str[:4000] + "…[truncated]"

                yield {
                    "type": "observation",
                    "step": step_count,
                    "tool": tool_name,
                    "result": json.loads(obs_str),
                    "success": result.get("success", False),
                    "latency_ms": latency_ms,
                }

                if tool_name == "calculator" and result.get("success"):
                    calc_results.append({
                        "expression": tool_args.get("expression", ""),
                        "value": result.get("data", {}).get("value"),
                        "units": tool_args.get("units") or "",
                    })
                if tool_name == "policy_retriever" and result.get("success"):
                    for p in result.get("data", {}).get("passages", []):
                        collected_citations.append({
                            "text":     p.get("text", ""),
                            "source":   p.get("source", pricing_url),
                            "captured": p.get("captured", capture_date),
                            "score":    p.get("score", 0),
                        })

                # Send tool result back
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": obs_str,
                })

            continue  # loop back to get next LLM response

        # No tool calls — model is done
        final_text = msg.content or ""
        stop_reason = "final_answer"
        yield {"type": "final_answer", "step": step_count, "content": final_text}
        break

    # Deduplicated citations
    seen: set[str] = set()
    unique_citations = []
    for c in collected_citations:
        key = c["text"][:80]
        if key not in seen:
            seen.add(key)
            unique_citations.append(c)

    if unique_citations:
        yield {
            "type": "citations",
            "items": sorted(unique_citations, key=lambda x: x["score"], reverse=True),
        }
    if calc_results:
        yield {"type": "calc_log", "items": calc_results}

    yield {
        "type": "metrics",
        "steps": step_count,
        "total_time_s": round(time.time() - start_time, 2),
        "stop_reason": stop_reason,
        "step_logs": step_logs,
    }
