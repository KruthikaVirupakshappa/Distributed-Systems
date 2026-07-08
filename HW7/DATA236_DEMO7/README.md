# DATA 236 Demo 7 - FastAPI JWT Authentication & Authorization

## Features
- JWT-based authentication
- Role-based authorization
- Protected routes
- Ruff linting
- pre-commit hook
- GitHub Actions CI

## Demo Users
- alice / alice123 -> student
- bob / bob123 -> instructor
- admin / admin123 -> admin

## Run
```bash
uvicorn app.main:app --reload