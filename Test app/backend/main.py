"""
Mock RAG gateway for the widget demo.

This stands in for your real FastAPI gateway (the one that will eventually
call your GCP Cloud Run RAG service). It fakes:
  - a small delay, like a real network + model call would have
  - session tracking in memory (in real life: Redis)
  - a couple of canned answers with citations, chosen by keyword match

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000
"""

import time
import uuid
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="RAG Widget Demo Gateway")

# CORS wide open here ONLY because this is a localhost demo running on a
# different port than the host page. In production, replace "*" with your
# real per-tenant allowlist (see the org_id -> allowed_domains config
# discussed earlier).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory stand-in for Redis session store.
SESSIONS: dict[str, dict] = {}

CANNED_ANSWERS = [
    {
        "keywords": ["refund", "return", "money back"],
        "answer": (
            "Refunds are available within 30 days of purchase. Once approved, "
            "it takes 5-7 business days for the amount to appear back on your "
            "original payment method."
        ),
        "citations": [
            {
                "id": "doc-101",
                "title": "Refund Policy v3.2",
                "snippet": "Customers may request a refund within 30 calendar days of the original purchase date...",
                "url": "https://example.com/policies/refunds.pdf",
            },
            {
                "id": "doc-102",
                "title": "Payment Processing Guide",
                "snippet": "Refunded amounts are returned via the original payment method within 5-7 business days...",
                "url": "https://example.com/policies/payments.html",
            },
        ],
    },
    {
        "keywords": ["password", "login", "sign in", "account"],
        "answer": (
            "You can reset your password from the sign-in page by selecting "
            "'Forgot password'. A reset link is valid for 15 minutes."
        ),
        "citations": [
            {
                "id": "doc-201",
                "title": "Account Security FAQ",
                "snippet": "Password reset links expire after 15 minutes for security reasons...",
                "url": "https://example.com/policies/account-security.html",
            },
        ],
    },
]

DEFAULT_ANSWER = {
    "answer": (
        "I don't have a specific policy document for that yet in this demo, "
        "but in the real system this is where the Vertex AI Search RAG "
        "pipeline would kick in with your actual document corpus."
    ),
    "citations": [],
}


class QueryRequest(BaseModel):
    session_id: Optional[str] = None
    question: str
    filters: Optional[dict] = None
    channel: Optional[str] = "widget"


class Citation(BaseModel):
    id: str
    title: str
    snippet: str
    url: str


class QueryResponse(BaseModel):
    session_id: str
    answer: str
    citations: list[Citation]
    latency_ms: int


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/query", response_model=QueryResponse)
def query(req: QueryRequest):
    start = time.time()

    # Session handling — stands in for the Redis session lookup/creation
    # your real gateway does.
    session_id = req.session_id or str(uuid.uuid4())
    history = SESSIONS.setdefault(session_id, {"turns": []})

    # Fake "model latency" so the demo feels like a real network call.
    time.sleep(0.6)

    question_lower = req.question.lower()
    match = next(
        (c for c in CANNED_ANSWERS if any(k in question_lower for k in c["keywords"])),
        None,
    )
    result = match or DEFAULT_ANSWER

    history["turns"].append({"question": req.question, "answer": result["answer"]})

    return QueryResponse(
        session_id=session_id,
        answer=result["answer"],
        citations=result["citations"],
        latency_ms=int((time.time() - start) * 1000),
    )
