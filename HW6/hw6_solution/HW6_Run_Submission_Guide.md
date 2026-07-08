# HW6 Run + Submission Guide

This file gives one end-to-end flow to run the app, recover from common issues, and capture deliverables.

## Part 0: Prerequisites

- Python env path (required):
  - `/Users/Kruthika/Documents/Data 236 Distributed Sys/env/bin/python`
- Project folder:
  - `/Users/Kruthika/Documents/Data 236 Distributed Sys/Homework/HW6/hw6_solution`
- Ollama models expected in `.env`:
  - `CHAT_MODEL=llama3.2:3b`
  - `EMBED_MODEL=nomic-embed-text`

## Part 1: Start Services + API

### 1. Open project directory

```bash
cd '/Users/Kruthika/Documents/Data 236 Distributed Sys/Homework/HW6/hw6_solution'
```

### 2. Ensure MongoDB is installed and running

```bash
brew services start mongodb-community
brew services list | grep -Ei 'mongo|mongodb'
lsof -nP -iTCP:27017 -sTCP:LISTEN
```

Expected:
- `mongodb-community started`
- `mongod` listening on `127.0.0.1:27017`

### 3. Ensure Ollama is running with required models

```bash
ollama list
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 4. Install dependencies (one-time or after updates)

```bash
"/Users/Kruthika/Documents/Data 236 Distributed Sys/env/bin/python" -m pip install -r requirements.txt
```

### 5. Start FastAPI app

```bash
"/Users/Kruthika/Documents/Data 236 Distributed Sys/env/bin/python" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/`

## Part 2: If Port Is Busy / Kill Process

### Check who uses port 8000

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

### Kill process on port 8000

```bash
kill -15 <PID>
# if it does not stop:
kill -9 <PID>
```

### Check MongoDB port 27017

```bash
lsof -nP -iTCP:27017 -sTCP:LISTEN
```

If MongoDB is down:

```bash
brew services restart mongodb-community
```

## Part 3: Screenshot Checklist

## Part 1 (Task API)

Use Swagger (`/docs`) and capture screenshots of:
1. `POST /api/tasks` success.
2. `GET /api/tasks` list with created task.
3. `GET /api/tasks/{id}` success.
4. `PUT /api/tasks/{id}` success.
5. `DELETE /api/tasks/{id}` success.
6. Validation failure (missing required field or invalid enum).

## Part 2 (Memory API)

Use Swagger (`/docs`) and capture screenshots of:
1. 8 to 10 calls to `POST /api/chat` with same `user_id` and same `session_id`.
2. `GET /api/memory/{user_id}` JSON showing recent messages, summaries, episodes.
3. `GET /api/aggregate/{user_id}` JSON showing daily counts + recent summaries.
4. MongoDB Compass collections with documents visible:
   - `tasks`
   - `messages`
   - `summaries`
   - `episodes`

## Part 4: Code Line Numbers To Cite (Current Version)

Use these file:line references in your report.

## Part 1 references

- App startup + CORS + validation handler + route registration:
  - `app/main.py:1`
  - `app/main.py:12`
  - `app/main.py:21`
  - `app/main.py:37`
  - `app/main.py:42`
- MongoDB connection + tasks schema validator + indexes:
  - `app/db.py:8`
  - `app/db.py:15`
  - `app/db.py:19`
  - `app/db.py:35`
  - `app/db.py:38`
  - `app/db.py:76`
- Task validation schemas:
  - `app/schemas.py:6`
  - `app/schemas.py:13`
  - `app/schemas.py:22`
  - `app/schemas.py:31`
- Task CRUD endpoints:
  - Create: `app/routes/tasks.py:11`
  - List: `app/routes/tasks.py:28`
  - Get by id: `app/routes/tasks.py:38`
  - Update: `app/routes/tasks.py:55`
  - Delete: `app/routes/tasks.py:81`

## Part 2 references

- Chat + memory endpoints:
  - `app/routes/memory.py:23` (`POST /api/chat`)
  - `app/routes/memory.py:87` (`GET /api/memory/{user_id}`)
  - `app/routes/memory.py:97` (`GET /api/aggregate/{user_id}`)
- Ollama integration (chat + embeddings):
  - `app/services/ollama_service.py:10`
  - `app/services/ollama_service.py:25`
  - `app/services/ollama_service.py:40`
- Memory logic:
  - Session id normalization: `app/services/memory_service.py:14`
  - Save/fetch short-term messages: `app/services/memory_service.py:20`, `app/services/memory_service.py:32`
  - Get latest summaries: `app/services/memory_service.py:51`
  - Episodic extraction: `app/services/memory_service.py:111`
  - Store episodes with embeddings: `app/services/memory_service.py:161`
  - Top-k episodic retrieval by cosine similarity: `app/services/memory_service.py:185`
  - Prompt assembly with long-term + short-term + episodic facts: `app/services/memory_service.py:222`
  - Session summary trigger every N user msgs: `app/services/memory_service.py:257`
  - Lifetime summary refresh: `app/services/memory_service.py:306`
  - Memory view response builder: `app/services/memory_service.py:350`
  - Aggregate daily message counts: `app/services/memory_service.py:378`

## Part 5: Quick Smoke Test Commands

### Create task

```bash
curl -X POST http://127.0.0.1:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Finish HW6",
    "description": "Complete part 1 and part 2",
    "status": "pending",
    "priority": "high",
    "dueDate": "2026-03-20T00:00:00Z",
    "category": "Work"
  }'
```

### Chat turn

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "kruthika",
    "session_id": "hw6-demo",
    "message": "I am preparing for distributed systems and need a weekly plan"
  }'
```

### Memory view

```bash
curl http://127.0.0.1:8000/api/memory/kruthika?session_id=hw6-demo
```

### Aggregate view

```bash
curl http://127.0.0.1:8000/api/aggregate/kruthika
```

## Part 6: Final Note

If line numbers shift after edits, regenerate line references with:

```bash
nl -ba app/main.py
nl -ba app/db.py
nl -ba app/routes/tasks.py
nl -ba app/routes/memory.py
nl -ba app/services/memory_service.py
nl -ba app/services/ollama_service.py
```
