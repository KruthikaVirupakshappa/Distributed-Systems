"""
Backend — HW10 Kafka GEval Pipeline
FastAPI + WebSocket + 3 Agents (Planner/Writer/Reviewer) + GEval scoring
Uses ollama directly (no langchain dependency).
"""

import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import ollama
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

# ── Config ────────────────────────────────────────────────────
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
OLLAMA_HOST     = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")

# ── Agent Definitions ─────────────────────────────────────────
AGENTS = {
    "planner": {
        "id": "planner", "name": "Planner", "emoji": "📋", "color": "#06b6d4",
        "consumes": "inbox", "produces": "tasks",
        "system_prompt": (
            "You are a Planner agent. Given a question, produce a clear numbered "
            "step-by-step TODO plan (3-5 steps) that a writer can follow to answer it. "
            "Be concise. Output only the numbered list, nothing else."
        ),
    },
    "writer": {
        "id": "writer", "name": "Writer", "emoji": "✍️", "color": "#f59e0b",
        "consumes": "tasks", "produces": "drafts",
        "system_prompt": (
            "You are a Writer agent. Given a question and a step-by-step plan, write a "
            "clear, concise answer (3-5 sentences) that directly addresses the question "
            "by following the plan. Use plain language. Output only the answer text."
        ),
    },
    "reviewer": {
        "id": "reviewer", "name": "Reviewer", "emoji": "✅", "color": "#10b981",
        "consumes": "drafts", "produces": "final",
        "system_prompt": (
            "You are a Reviewer agent. Evaluate the answer for accuracy and clarity. "
            "Respond with ONLY a valid JSON object — no markdown, no extra text:\n"
            '{"status": "approved", "answer": "<the answer verbatim>", "feedback": "<brief feedback>"}'
        ),
    },
}
AGENT_PIPELINE = ["planner", "writer", "reviewer"]


# ── WebSocket Manager ─────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []
        self.event_log: list[dict] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
        for event in self.event_log:
            await ws.send_json(event)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, event: dict):
        self.event_log.append(event)
        if len(self.event_log) > 500:
            self.event_log = self.event_log[-500:]
        dead = []
        for ws in self.connections:
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connections.remove(ws)


manager = ConnectionManager()
producer: Optional[AIOKafkaProducer] = None


# ── Kafka Producer ─────────────────────────────────────────────
async def create_producer():
    global producer
    for attempt in range(10):
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_serializer=lambda v: json.dumps(v).encode(),
            )
            await producer.start()
            print("✔ Kafka producer connected")
            return
        except Exception as e:
            print(f"✘ Producer attempt {attempt + 1}: {e}")
            await asyncio.sleep(3)


async def publish(topic: str, message: dict):
    if producer:
        await producer.send_and_wait(topic, message)


# ── Ollama LLM call ────────────────────────────────────────────
async def agent_think(agent_id: str, data: dict) -> str:
    agent = AGENTS[agent_id]
    question = data.get("question", "")
    plan     = data.get("plan", "")
    draft    = data.get("draft", data.get("answer", ""))

    if agent_id == "planner":
        user_content = f"Question: {question}"
    elif agent_id == "writer":
        user_content = f"Question: {question}\n\nPlan:\n{plan}\n\nWrite the answer now."
    else:
        user_content = f"Question: {question}\n\nAnswer to review:\n{draft}"

    def _call():
        client = ollama.Client(host=OLLAMA_HOST)
        resp = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": agent["system_prompt"]},
                {"role": "user",   "content": user_content},
            ],
        )
        return resp["message"]["content"].strip()

    return await asyncio.to_thread(_call)


# ── GEval Judge (Ollama) ───────────────────────────────────────
class OllamaJudge(DeepEvalBaseLLM):
    def load_model(self): return OLLAMA_MODEL

    def generate(self, prompt: str, schema=None) -> str:
        client = ollama.Client(host=OLLAMA_HOST)
        kwargs = {"model": OLLAMA_MODEL, "messages": [{"role": "user", "content": prompt}]}
        if schema is not None:
            kwargs["format"] = "json"
        return client.chat(**kwargs)["message"]["content"]

    async def a_generate(self, prompt: str, schema=None) -> str:
        return await asyncio.to_thread(self.generate, prompt, schema)

    def get_model_name(self) -> str:
        return f"ollama/{OLLAMA_MODEL}"


def run_geval(question: str, plan: str, draft: str, final_answer: str) -> dict:
    judge = OllamaJudge()

    metrics = {
        "Plan-Quality": GEval(
            name="Plan-Quality",
            criteria=(
                "Evaluate whether the ACTUAL_OUTPUT is a clear, numbered, actionable "
                "step-by-step plan that would help someone answer the INPUT question."
            ),
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            model=judge,
        ),
        "Writer-Helpfulness": GEval(
            name="Writer-Helpfulness",
            criteria=(
                "Determine whether the ACTUAL_OUTPUT directly and completely answers "
                "the INPUT question in clear, concise language."
            ),
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            model=judge,
        ),
        "Reviewer-Helpfulness": GEval(
            name="Reviewer-Helpfulness",
            criteria=(
                "Determine whether the ACTUAL_OUTPUT (Reviewer's final answer) "
                "directly and completely addresses the INPUT question."
            ),
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            model=judge,
        ),
        "Final-vs-Draft": GEval(
            name="Final-vs-Draft",
            evaluation_steps=[
                "EXPECTED_OUTPUT is the Writer's draft. ACTUAL_OUTPUT is the Reviewer's final answer.",
                "Score 1.0 if clearly improved, 0.5 if same quality, 0.0 if worse.",
            ],
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
            model=judge,
        ),
    }

    scores = {}
    metrics["Plan-Quality"].measure(LLMTestCase(input=question, actual_output=plan))
    scores["Plan-Quality"] = {"score": round(float(metrics["Plan-Quality"].score or 0), 2),
                               "reason": metrics["Plan-Quality"].reason or ""}

    metrics["Writer-Helpfulness"].measure(LLMTestCase(input=question, actual_output=draft))
    scores["Writer-Helpfulness"] = {"score": round(float(metrics["Writer-Helpfulness"].score or 0), 2),
                                     "reason": metrics["Writer-Helpfulness"].reason or ""}

    metrics["Reviewer-Helpfulness"].measure(LLMTestCase(input=question, actual_output=final_answer))
    scores["Reviewer-Helpfulness"] = {"score": round(float(metrics["Reviewer-Helpfulness"].score or 0), 2),
                                       "reason": metrics["Reviewer-Helpfulness"].reason or ""}

    metrics["Final-vs-Draft"].measure(LLMTestCase(input=question, actual_output=final_answer, expected_output=draft))
    scores["Final-vs-Draft"] = {"score": round(float(metrics["Final-vs-Draft"].score or 0), 2),
                                 "reason": metrics["Final-vs-Draft"].reason or ""}

    return scores


# ── Agent Consumer Loop ────────────────────────────────────────
pipeline_data: dict = {}


async def run_agent(agent_id: str):
    agent = AGENTS[agent_id]
    topic = agent["consumes"]
    out_topic = agent["produces"]

    for attempt in range(15):
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_deserializer=lambda v: json.loads(v.decode()),
                group_id=f"hw10-{agent_id}-group",
                auto_offset_reset="latest",
            )
            await consumer.start()
            print(f"✔ Agent [{agent['name']}] listening on '{topic}'")
            break
        except Exception as e:
            print(f"✘ Consumer {agent_id} attempt {attempt + 1}: {e}")
            await asyncio.sleep(3)
    else:
        return

    try:
        async for msg in consumer:
            data = msg.value
            correlation_id = data.get("correlation_id", str(uuid.uuid4()))
            question = data.get("question", "")
            if not question:
                continue

            print(f"[{agent['name']}] ← Received [{correlation_id[:8]}]")

            await manager.broadcast({
                "type": "agent_start", "agent": agent_id,
                "correlation_id": correlation_id, "timestamp": datetime.utcnow().isoformat(),
            })
            await manager.broadcast({
                "type": "agent_thinking", "agent": agent_id,
                "correlation_id": correlation_id, "timestamp": datetime.utcnow().isoformat(),
            })

            result = await agent_think(agent_id, data)

            await manager.broadcast({
                "type": "agent_complete", "agent": agent_id,
                "correlation_id": correlation_id, "content": result,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Build outgoing message
            out_msg: dict = {"correlation_id": correlation_id, "question": question}

            if agent_id == "planner":
                out_msg["plan"] = result
                pipeline_data[correlation_id] = {"question": question, "plan": result}

            elif agent_id == "writer":
                out_msg["plan"]  = data.get("plan", "")
                out_msg["draft"] = result
                if correlation_id in pipeline_data:
                    pipeline_data[correlation_id]["draft"] = result

            else:  # reviewer
                try:
                    parsed = json.loads(result)
                except json.JSONDecodeError:
                    parsed = {"status": "approved", "answer": data.get("draft", result), "feedback": result}
                out_msg.update(parsed)
                out_msg["draft"] = data.get("draft", "")
                final_answer = parsed.get("answer", data.get("draft", result))
                if correlation_id in pipeline_data:
                    pipeline_data[correlation_id]["final_answer"] = final_answer

            await manager.broadcast({
                "type": "kafka_message", "from_agent": agent_id,
                "to_topic": out_topic, "correlation_id": correlation_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

            await publish(out_topic, out_msg)

            if agent_id == "reviewer":
                await manager.broadcast({
                    "type": "pipeline_complete", "correlation_id": correlation_id,
                    "final_output": out_msg, "timestamp": datetime.utcnow().isoformat(),
                })

                # Run GEval in background thread
                trace = pipeline_data.get(correlation_id, {})
                if trace.get("plan") and trace.get("draft"):
                    asyncio.create_task(run_geval_and_broadcast(
                        correlation_id,
                        trace["question"],
                        trace["plan"],
                        trace["draft"],
                        trace.get("final_answer", trace["draft"]),
                    ))
    finally:
        await consumer.stop()


async def run_geval_and_broadcast(correlation_id, question, plan, draft, final_answer):
    try:
        await manager.broadcast({
            "type": "geval_start", "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        scores = await asyncio.to_thread(run_geval, question, plan, draft, final_answer)
        await manager.broadcast({
            "type": "geval_complete", "correlation_id": correlation_id,
            "scores": scores, "timestamp": datetime.utcnow().isoformat(),
        })
        print(f"[GEval] Scores for [{correlation_id[:8]}]: {scores}")
    except Exception as e:
        print(f"[GEval] Error: {e}")
        await manager.broadcast({
            "type": "geval_error", "correlation_id": correlation_id,
            "error": str(e), "timestamp": datetime.utcnow().isoformat(),
        })


# ── FastAPI App ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_producer()
    tasks = [asyncio.create_task(run_agent(aid)) for aid in AGENT_PIPELINE]
    yield
    for t in tasks:
        t.cancel()
    if producer:
        await producer.stop()


app = FastAPI(title="HW10 Kafka GEval Pipeline", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class TaskRequest(BaseModel):
    question: str = "What is the CAP theorem in distributed systems?"


@app.post("/api/task")
async def submit_task(req: TaskRequest):
    correlation_id = str(uuid.uuid4())
    await manager.broadcast({
        "type": "task_submitted", "correlation_id": correlation_id,
        "question": req.question, "timestamp": datetime.utcnow().isoformat(),
    })
    await publish("inbox", {"correlation_id": correlation_id, "question": req.question})
    return {"correlation_id": correlation_id, "status": "submitted"}


@app.get("/api/health")
async def health():
    return {"status": "ok", "kafka": KAFKA_BOOTSTRAP}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(ws)
