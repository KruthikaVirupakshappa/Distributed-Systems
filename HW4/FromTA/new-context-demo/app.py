

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

DEMO_DIR = Path(__file__).resolve().parent

load_dotenv(DEMO_DIR.parent / ".env")
load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────


class ScenarioInputs(BaseModel):
    """
    The raw material — the actual Python bug being debugged.

    Pre-filled with the classic "discount applied after tax" gotcha.
    Instructors can swap any field to change the scenario.
    """

    test_name: str = Field(default="test_total_price_includes_tax")

    test_code: str = Field(
        default=(
            "def test_total_price_includes_tax():\n"
            "    price = calculate_total_price(100, tax_rate=0.1, discount=0.05)\n"
            "    assert price == 104.5  # expected: 100 * 0.95 (discount first) * 1.1 (then tax)"
        )
    )

    implementation_code: str = Field(
        default=(
            "def calculate_total_price(base, tax_rate, discount):\n"
            "    # BUG introduced by refactor: discount is now applied AFTER tax\n"
            "    with_tax = base * (1 + tax_rate)\n"
            "    return with_tax * (1 - discount)"
        )
    )

    error_output: str = Field(
        default=(
            "FAILED test_pricing.py::test_total_price_includes_tax\n"
            "AssertionError: assert 99.275 == 104.5\n"
            "  Actual:   99.275  =  100 * 1.1 * 0.95   (tax applied first)\n"
            "  Expected: 104.5   =  100 * 0.95 * 1.1   (discount applied first)"
        )
    )


class ContextIngredients(BaseModel):
    """
    The engineerable layer — what YOU add on top of the raw code.

    These fields only affect Experiment 3.
    Changing them and re-running shows students how context shapes model
    behaviour without changing the underlying bug at all.

    This is the core lesson: model output = f(context). You own the context.
    """

    system_role: str = Field(
        default=(
            "You are a calm, patient AI tutor for a Data Engineering course. "
            "Always identify the root cause in plain language before showing code. "
            "Keep all suggested changes minimal."
        ),
        description="Defines WHO the model is — persona, tone, and non-negotiable behaviour.",
    )

    student_background: str = Field(
        default=(
            "The student understands Python basics and knows what a unit test is, "
            "but has never thought about arithmetic order in price calculations. "
            "They are frustrated and said: 'I just want the test to pass!'"
        ),
        description="Calibrates explanation depth and vocabulary to the actual learner.",
    )

    conversation_history: str = Field(
        default=(
            "Student shared the failing assertion 5 minutes ago. "
            "You already asked them to paste the implementation, which they did. "
            "They confirmed the function passed all tests before the refactor yesterday."
        ),
        description="Prevents repetition and gives the model continuity across turns.",
    )

    constraints: str = Field(
        default=(
            "- Do NOT suggest large refactors or new parameters.\n"
            "- Explain the root cause in 1-2 plain-language sentences first.\n"
            "- Show ONLY the changed line(s), not the full function.\n"
            "- End with one sentence confirming what the fix achieves."
        ),
        description="Hard rules that control output format, scope, and length.",
    )


class RunRequest(BaseModel):
    """Full experiment request: scenario + context ingredients."""

    scenario: ScenarioInputs = Field(default_factory=ScenarioInputs)
    ingredients: ContextIngredients = Field(default_factory=ContextIngredients)


class ExperimentResult(BaseModel):
    """What one experiment produced."""

    key: str
    label: str
    tag: str           # short classifier shown as a badge in the UI
    philosophy: str    # one-sentence description of what this context strategy does
    what_changed: str  # explicit diff from the previous experiment
    context_sent: str  # the actual prompt sent — shown in a collapsible for transparency
    reply: str
    prompt_tokens: int
    completion_tokens: int


class RunResponse(BaseModel):
    experiments: List[ExperimentResult]


# ─────────────────────────────────────────────────────────────────────────────
# Context builders — this is where the "engineering" happens
# ─────────────────────────────────────────────────────────────────────────────


def _build_bare_messages(s: ScenarioInputs) -> list:
    
    return [
        {
            "role": "user",
            "content": (
                f"My test `{s.test_name}` is failing after a refactor. "
                "Can you help me fix it?"
            ),
        }
    ]


def _build_code_messages(s: ScenarioInputs) -> list:

    return [
        {
            "role": "system",
            "content": "You are a helpful coding assistant.",
        },
        {
            "role": "user",
            "content": (
                f"My test `{s.test_name}` is failing. Here is the relevant code:\n\n"
                f"**Test:**\n```python\n{s.test_code}\n```\n\n"
                f"**Current implementation:**\n```python\n{s.implementation_code}\n```\n\n"
                f"**Error output:**\n```\n{s.error_output}\n```\n\n"
                "What is wrong, and how do I fix it?"
            ),
        },
    ]


def _build_engineered_messages(s: ScenarioInputs, i: ContextIngredients) -> list:
   
    system_content = (
        f"{i.system_role.strip()}\n\n"
        f"[STUDENT BACKGROUND]\n{i.student_background.strip()}\n\n"
        f"[CONVERSATION SO FAR]\n{i.conversation_history.strip()}\n\n"
        f"[HARD CONSTRAINTS — follow these exactly]\n{i.constraints.strip()}"
    )

    user_content = (
        f"[FAILING TEST]\n```python\n{s.test_code}\n```\n\n"
        f"[CURRENT IMPLEMENTATION]\n```python\n{s.implementation_code}\n```\n\n"
        f"[ERROR OUTPUT]\n```\n{s.error_output}\n```\n\n"
        "Why is this failing, and what is the smallest possible fix?"
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Context Engineering Lab")


@app.get("/", response_class=HTMLResponse)
def index() -> FileResponse:
    return FileResponse(DEMO_DIR / "index.html")


def _messages_to_str(messages: list) -> str:
    """Serialise the messages list into readable text for UI transparency panels."""
    parts = []
    for m in messages:
        role = m.get("role", "?").upper()
        content = m.get("content", "")
        parts.append(f"[{role}]\n{content}")
    return "\n\n".join(parts)


def _call_openai(messages: list, model: str, api_key: str) -> dict:
    """
    Single OpenAI chat completion call.

    Temperature is kept low (0.3) so results are consistent across classroom demos.
    In production you would tune this per use-case.
    """
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=600,
        temperature=0.3,
    )
    choice = response.choices[0] if response.choices else None
    usage = response.usage
    return {
        "reply": (
            choice.message.content
            if choice and choice.message
            else "(no reply returned)"
        ),
        "prompt_tokens": usage.prompt_tokens if usage else 0,
        "completion_tokens": usage.completion_tokens if usage else 0,
    }


@app.post("/api/run-experiments", response_model=RunResponse)
def run_experiments(req: RunRequest) -> RunResponse:
    """
    Run the same debugging scenario through three different context designs.

    Calls OpenAI three times sequentially.
    Returns all three results plus instructor teaching notes.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "OPENAI_API_KEY is not set. "
                "Add it to the .env file in the project root and restart."
            ),
        )

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()

    specs = [
        {
            "key": "bare",
            "label": "Experiment 1 · No Context",
            "tag": "no context",
            "philosophy": (
                "The model receives only the question — no code, no role, no history. "
                "This is the default 'just ask ChatGPT' approach."
            ),
            "what_changed": "Starting point. Nothing has been added yet.",
            "build": lambda: _build_bare_messages(req.scenario),
        },
        {
            "key": "code",
            "label": "Experiment 2 · Code Context Added",
            "tag": "code context",
            "philosophy": (
                "System prompt + test + implementation + error output added. "
                "The model now has the facts it needs to find the bug."
            ),
            "what_changed": (
                "Added: system prompt, the test body, the implementation, and the error output. "
                "The model can now reason about the specific bug — but tone and format are still unguided."
            ),
            "build": lambda: _build_code_messages(req.scenario),
        },
        {
            "key": "engineered",
            "label": "Experiment 3 · Fully Engineered",
            "tag": "engineered",
            "philosophy": (
                "Role + student background + conversation history + constraints added on top of the code. "
                "Every token serves a deliberate purpose."
            ),
            "what_changed": (
                "Added on top of Experiment 2: detailed system role (persona + tone), "
                "student background (calibrates explanation depth), "
                "conversation history (prevents repetition), "
                "and hard constraints (controls output format and scope). "
                "The bug facts are IDENTICAL to Experiment 2."
            ),
            "build": lambda: _build_engineered_messages(req.scenario, req.ingredients),
        },
    ]

    results: List[ExperimentResult] = []
    for spec in specs:
        messages = spec["build"]()
        try:
            out = _call_openai(messages, model, api_key)
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"OpenAI error in {spec['key']}: {str(exc)}",
            ) from exc

        results.append(
            ExperimentResult(
                key=spec["key"],
                label=spec["label"],
                tag=spec["tag"],
                philosophy=spec["philosophy"],
                what_changed=spec["what_changed"],
                context_sent=_messages_to_str(messages),
                reply=out["reply"],
                prompt_tokens=out["prompt_tokens"],
                completion_tokens=out["completion_tokens"],
            )
        )

    return RunResponse(experiments=results)


@app.get("/health", response_class=HTMLResponse)
def health() -> str:
    return "ok"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
