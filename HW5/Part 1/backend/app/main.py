from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers import authors, books

app = FastAPI(title="Library Management API")

# Frontend is on http://localhost:3006
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3006"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    # Keeps backend minimal: auto-creates tables if missing
    Base.metadata.create_all(bind=engine)

app.include_router(authors.router)
app.include_router(books.router)

@app.get("/")
def health():
    return {"status": "ok"}