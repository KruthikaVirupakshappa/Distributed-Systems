"""
Multi-Agent Collaboration Demo
─────────────────────────────
Agents communicate via Kafka topics. A WebSocket broadcasts all events
to the frontend visualization in real time.

Architecture:
  User ──► [agent-tasks] ──► Researcher ──► [agent-research]
                                               │
                              Analyst ◄────────┘
                                │
                           [agent-analysis]
                                │
                              Writer ◄─────────┘
                                │
                           [agent-writing]
                                │
                             Reviewer ◄────────┘
                                │
                           [agent-review] ──► Final Output
"""

import asyncio
import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Configuration ───────────────────────────────────────────
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from openai import AsyncOpenAI
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# ── Agent Definitions ──────────────────────────────────────
AGENTS = {
    "researcher": {
        "id": "researcher",
        "name": "Researcher",
        "emoji": "",
        "color": "#06b6d4",
        "consumes": "agent-tasks",
        "produces": "agent-research",
        "system_prompt": (
            "You are a Research Agent. Given a topic, provide 3-4 key findings "
            "with brief evidence. Be concise and factual. Max 150 words."
        ),
    },
    "analyst": {
        "id": "analyst",
        "name": "Analyst",
        "emoji": "",
        "color": "#8b5cf6",
        "consumes": "agent-research",
        "produces": "agent-analysis",
        "system_prompt": (
            "You are an Analysis Agent. Given research findings, extract insights, "
            "identify patterns, and provide a structured analysis. Max 150 words."
        ),
    },
    "writer": {
        "id": "writer",
        "name": "Writer",
        "emoji": "",
        "color": "#f59e0b",
        "consumes": "agent-analysis",
        "produces": "agent-writing",
        "system_prompt": (
            "You are a Writing Agent. Given analysis, compose a polished executive "
            "briefing paragraph. Professional tone, clear and actionable. Max 120 words."
        ),
    },
    "reviewer": {
        "id": "reviewer",
        "name": "Reviewer",
        "emoji": "",
        "color": "#10b981",
        "consumes": "agent-writing",
        "produces": "agent-review",
        "system_prompt": (
            "You are a Review Agent. Evaluate the draft for accuracy, clarity, and "
            "actionability. Provide a quality score (1-10) and brief feedback. Max 100 words."
        ),
    },
}

AGENT_PIPELINE = ["researcher", "analyst", "writer", "reviewer"]


# ── WebSocket Manager ──────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []
        self.event_log: list[dict] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
        # Send full event history to new connections
        for event in self.event_log:
            await ws.send_json(event)

    def disconnect(self, ws: WebSocket):
        self.connections.remove(ws)

    async def broadcast(self, event: dict):
        self.event_log.append(event)
        # Keep last 500 events
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


# ── Kafka Helpers ──────────────────────────────────────────
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
            print(" Kafka producer connected")
            return
        except Exception as e:
            print(f" Producer attempt {attempt+1}: {e}")
            await asyncio.sleep(3)


async def publish(topic: str, message: dict):
    if producer:
        await producer.send_and_wait(topic, message)


# ── Agent LLM Call ─────────────────────────────────────────
async def agent_think(agent_id: str, input_text: str) -> str:
    """Call OpenAI for agent response."""
    agent = AGENTS[agent_id]
    
    resp = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": agent["system_prompt"]},
            {"role": "user", "content": input_text},
        ],
        max_tokens=300,
        temperature=0.7,
    )
    return resp.choices[0].message.content


# ── Agent Consumer Loop ────────────────────────────────────
async def run_agent(agent_id: str):
    """Each agent consumes from its topic, thinks, and produces to the next."""
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
            print(f" Agent [{agent['name']}] listening on '{topic}'")
            break
        except Exception as e:
            print(f" Consumer {agent_id} attempt {attempt+1}: {e}")
            await asyncio.sleep(3)
    else:
        print(f" Agent [{agent['name']}] failed to connect")
        return

    try:
        async for msg in consumer:
            data = msg.value
            task_id = data.get("task_id", str(uuid.uuid4()))
            input_text = data.get("content", "")

            # Broadcast: agent started
            await manager.broadcast({
                "type": "agent_start",
                "agent": agent_id,
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Broadcast agent thinking status
            await manager.broadcast({
                "type": "agent_thinking",
                "agent": agent_id,
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Do the actual work
            result = await agent_think(agent_id, input_text)

            # Broadcast: agent completed
            await manager.broadcast({
                "type": "agent_complete",
                "agent": agent_id,
                "task_id": task_id,
                "content": result,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Broadcast: message sent to next topic
            await manager.broadcast({
                "type": "kafka_message",
                "from_agent": agent_id,
                "to_topic": out_topic,
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Publish result to next agent's topic
            await publish(out_topic, {
                "task_id": task_id,
                "content": result,
                "from_agent": agent_id,
            })

            # If this is the reviewer, broadcast pipeline complete
            if agent_id == "reviewer":
                await manager.broadcast({
                    "type": "pipeline_complete",
                    "task_id": task_id,
                    "final_output": result,
                    "timestamp": datetime.utcnow().isoformat(),
                })
    finally:
        await consumer.stop()


# ── FastAPI App ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_producer()
    # Launch all agent consumer loops
    tasks = [asyncio.create_task(run_agent(aid)) for aid in AGENT_PIPELINE]
    yield
    for t in tasks:
        t.cancel()
    if producer:
        await producer.stop()


app = FastAPI(title="Multi-Agent Collaboration Demo", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskRequest(BaseModel):
    topic: str = "The future of multi-agent AI systems"


@app.post("/api/task")
async def submit_task(req: TaskRequest):
    """Submit a new task into the agent pipeline."""
    task_id = str(uuid.uuid4())[:8]

    await manager.broadcast({
        "type": "task_submitted",
        "task_id": task_id,
        "topic": req.topic,
        "timestamp": datetime.utcnow().isoformat(),
    })

    await publish("agent-tasks", {
        "task_id": task_id,
        "content": f"Research and analyze this topic: {req.topic}",
    })

    return {"task_id": task_id, "status": "submitted"}


@app.get("/api/agents")
async def get_agents():
    """Return agent definitions for the UI."""
    return {
        aid: {
            "id": a["id"],
            "name": a["name"],
            "emoji": a["emoji"],
            "color": a["color"],
            "consumes": a["consumes"],
            "produces": a["produces"],
        }
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
            # Keep connection alive; client can also send commands
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(ws)
