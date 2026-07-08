# 3-Agent Mini-System with Kafka + LangChain

A multi-agent system where three AI agents communicate exclusively through Apache Kafka topics. No agent calls another agent directly — all coordination happens via message passing.

## Pipeline

```
You → [inbox] → Planner → [tasks] → Writer → [drafts] → Reviewer → [final]
```

| Agent    | Reads From | Writes To | Role |
|----------|-----------|-----------|------|
| Planner  | `inbox`   | `tasks`   | Creates a step-by-step TODO plan for the question |
| Writer   | `tasks`   | `drafts`  | Writes a short answer using LangChain |
| Reviewer | `drafts`  | `final`   | Reviews and approves the answer |

## Tech Stack

- **Apache Kafka** — message broker between agents
- **LangChain + Ollama (llama3.2)** — local LLM, runs for free
- **FastAPI + WebSocket** — backend API and real-time event streaming
- **React** — live visualization dashboard
- **Docker Compose** — orchestrates all services

## Project Structure

```
Kafka-Multi-Agent/
├── backend/
│   ├── main.py          # FastAPI + 3 agents + WebSocket
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/App.js       # Real-time dashboard
│   ├── public/
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── planner.py           # Standalone Planner agent
├── writer.py            # Standalone Writer agent
├── reviewer.py          # Standalone Reviewer agent
└── send_question.py     # Sends a question to kick off the pipeline
```

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Ollama](https://ollama.com) with `llama3.2` model pulled:
  ```bash
  ollama pull llama3.2
  ```

## Option A — Run with Docker Compose (Full UI)

```bash
docker-compose up --build
```

Open **http://localhost:3000** to see the live dashboard, type a question, and click **▶ Ask Agents**.

## Option B — Run in Separate Terminals

Make sure Kafka is running first:
```bash
docker-compose up -d zookeeper kafka kafka-init
```

Activate the virtual environment:
```bash
source path/to/env/bin/activate
```

**Terminal 1 — Planner:**
```bash
python planner.py
```

**Terminal 2 — Writer:**
```bash
python writer.py
```

**Terminal 3 — Reviewer:**
```bash
python reviewer.py
```

**Terminal 4 — Send a question:**
```bash
python send_question.py "What is the CAP theorem?"
```

## View the Final Result

```bash
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic final \
  --from-beginning
```

Expected output:
```json
{"status": "approved", "answer": "...", "feedback": "..."}
```

## How Kafka Helps Agents Coordinate

Each agent is fully decoupled — no agent holds a reference to another. Kafka topics act as persistent message queues between them. If an agent restarts, Kafka holds the message until the agent is ready to consume it. This makes the system fault-tolerant, scalable, and easy to extend with additional agents.
