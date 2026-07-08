# Homework 6 Solution (FastAPI + PyMongo + Ollama)

## Run with your existing env

From workspace root:

```bash
"/Users/Kruthika/Documents/Data 236 Distributed Sys/env/bin/python" -m pip install -r "Homework/HW6/hw6_solution/requirements.txt"
"/Users/Kruthika/Documents/Data 236 Distributed Sys/env/bin/python" -m uvicorn app.main:app --reload --app-dir "Homework/HW6/hw6_solution"
```

## Endpoints

- `POST /api/tasks`
- `GET /api/tasks`
- `GET /api/tasks/{id}`
- `PUT /api/tasks/{id}`
- `DELETE /api/tasks/{id}`

- `POST /api/chat`
- `GET /api/memory/{user_id}`
- `GET /api/aggregate/{user_id}`

## Notes

- Uses one MongoDB database (`MONGODB_DB`) with collections: `tasks`, `messages`, `summaries`, `episodes`.
- `tasks` validator is configured at startup (best effort).
- Part 2 memory logic includes:
  - short-term message window,
  - session/lifetime summaries,
  - episodic extraction + embeddings + cosine retrieval.
