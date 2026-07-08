"""
3-Agent Mini-System with Kafka + LangChain
──────────────────────────────────────────
Agents communicate via Kafka topics. A WebSocket broadcasts all events
to the frontend visualization in real time.

Pipeline:
  User ──► [inbox] ──► Planner ──► [tasks] ──► Writer ──► [drafts] ──► Reviewer ──► [final]

  Planner : Makes a step-by-step TODO plan for the question.
  Writer  : Writes a short answer using LangChain.
  Reviewer: Checks the answer and approves it → {"status": "approved", "answer": "..."}
"""

import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel

# ── Configuration ────────────────────────────────────────────
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# ── Agent Definitions ─────────────────────────────────────────
AGENTS = {
    "planner": {
        "id": "planner",
        "name": "Planner",
        "emoji": "📋",
        "color": "#06b6d4",
        "consumes": "inbox",
        "produces": "tasks",
        "system_prompt": (
            "You are a Planner agent. Given a question, produce a clear numbered "
            "step-by-step TODO plan (3-5 steps) that a writer can follow to answer it. "
            "Be concise. Output only the numbered list, nothing else."
        ),
    },
    "writer": {
        "id": "writer",
        "name": "Writer",
        "emoji": "✍️",
        "color": "#f59e0b",
        "consumes": "tasks",
        "produces": "drafts",
        "system_prompt": (
            "You are a Writer agent. Given a question and a step-by-step plan, write a "
            "clear, concise answer (3-5 sentences) that directly addresses the question "
            "by following the plan. Use plain language. Output only the answer text."
        ),
    },
    "reviewer": {
        "id": "reviewer",
        "name": "Reviewer",
        "emoji": "✅",
        "color": "#10b981",
        "consumes": "drafts",
        "produces": "final",
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

# ── Kafka Producer ─────────────────────────────────────────────
producer: Optional[AIOKafkaProducer] = None


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


# ── LangChain LLM ─────────────────────────────────────────────
def get_llm(temperature: float = 0.4) -> ChatOllama:
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
    )


async def agent_think(agent_id: str, data: dict) -> str:
    """Build the prompt per agent and call LangChain asynchronously."""
    agent = AGENTS[agent_id]
    question = data.get("question", "")
    plan = data.get("plan", "")
    answer = data.get("answer", "")
    print(f"[{agent['name']}] Calling OpenAI... question={question[:60]}")

    if agent_id == "planner":
        user_content = f"Question: {question}"
        temperature = 0.3
    elif agent_id == "writer":
        user_content = (
            f"Question: {question}\n\n"
            f"Plan to follow:\n{plan}\n\n"
            "Write the answer now."
        )
        temperature = 0.5
    else:  # reviewer
        user_content = (
            f"Question: {question}\n\n"
            f"Answer to review:\n{answer}"
        )
        temperature = 0.2

    llm = get_llm(temperature)
    messages = [
        SystemMessage(content=agent["system_prompt"]),
        HumanMessage(content=user_content),
    ]
    response = await asyncio.wait_for(llm.ainvoke(messages), timeout=60)
    print(f"[{agent['name']}] OpenAI responded.")
    return response.content.strip()


# ── Agent Consumer Loop ────────────────────────────────────────
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
                group_id=f"{agent_id}-group",
                auto_offset_reset="earliest",
            )
            await consumer.start()
            print(f"✔ Agent [{agent['name']}] listening on '{topic}'")
            break
        except Exception as e:
            print(f"✘ Consumer {agent_id} attempt {attempt + 1}: {e}")
            await asyncio.sleep(3)
    else:
        print(f"✘ Agent [{agent['name']}] failed to connect — giving up")
        return

    try:
        async for msg in consumer:
            data = msg.value
            task_id = data.get("task_id", str(uuid.uuid4())[:8])
            print(f"[{agent['name']}] ← Message received on '{topic}'")

            # Broadcast: agent started
            await manager.broadcast({
                "type": "agent_start",
                "agent": agent_id,
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Broadcast: agent thinking
            await manager.broadcast({
                "type": "agent_thinking",
                "agent": agent_id,
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Do the work
            result = await agent_think(agent_id, data)

            # Broadcast: agent completed
            await manager.broadcast({
                "type": "agent_complete",
                "agent": agent_id,
                "task_id": task_id,
                "content": result,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Build the outgoing message for the next agent
            out_msg: dict = {"task_id": task_id, "from_agent": agent_id}

            if agent_id == "planner":
                out_msg["question"] = data.get("question", "")
                out_msg["plan"] = result
            elif agent_id == "writer":
                out_msg["question"] = data.get("question", "")
                out_msg["plan"] = data.get("plan", "")
                out_msg["answer"] = result
            else:  # reviewer — parse JSON or wrap raw text
                try:
                    parsed = json.loads(result)
                    out_msg.update(parsed)
                except json.JSONDecodeError:
                    out_msg["status"] = "approved"
                    out_msg["answer"] = data.get("answer", result)
                    out_msg["feedback"] = result

            # Broadcast: kafka message sent
            await manager.broadcast({
                "type": "kafka_message",
                "from_agent": agent_id,
                "to_topic": out_topic,
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

            await publish(out_topic, out_msg)

            # Reviewer = pipeline complete
            if agent_id == "reviewer":
                await manager.broadcast({
                    "type": "pipeline_complete",
                    "task_id": task_id,
                    "final_output": out_msg,
                    "timestamp": datetime.utcnow().isoformat(),
                })
    finally:
        await consumer.stop()


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


app = FastAPI(title="3-Agent Kafka + LangChain Demo", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskRequest(BaseModel):
    question: str = "What is distributed computing and why is it important?"


@app.post("/api/task")
async def submit_task(req: TaskRequest):
    task_id = str(uuid.uuid4())[:8]

    await manager.broadcast({
        "type": "task_submitted",
        "task_id": task_id,
        "question": req.question,
        "timestamp": datetime.utcnow().isoformat(),
    })

    await publish("inbox", {
        "task_id": task_id,
        "question": req.question,
    })

    return {"task_id": task_id, "status": "submitted"}


@app.get("/api/agents")
async def get_agents():
    return {
        aid: {k: v for k, v in a.items() if k != "system_prompt"}
        for aid, a in AGENTS.items()
    }


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
