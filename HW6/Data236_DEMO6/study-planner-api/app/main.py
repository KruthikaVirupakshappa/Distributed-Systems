from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.sessions import router as sessions_router

app = FastAPI(title="Study Planner API (FastAPI + PyMongo)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router)

@app.get("/")
def health():
    return {"status": "ok", "message": "Study Planner API is running"}