from fastapi import APIRouter, HTTPException
from pymongo.errors import PyMongoError

from ..config import settings
from ..schemas import AggregateResponse, ChatRequest, ChatResponse, MemoryViewResponse
from ..services.memory_service import (
    aggregate_user_activity,
    build_chat_messages,
    get_latest_summary,
    get_recent_messages,
    load_memory_view,
    maybe_refresh_summaries,
    normalize_session_id,
    retrieve_relevant_episodes,
    save_message,
    store_episodes_for_message,
)
from ..services.ollama_service import OllamaError, chat as ollama_chat

router = APIRouter(prefix="/api", tags=["Memory"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    session_id = normalize_session_id(payload.session_id)

    try:
        save_message(payload.user_id, session_id, "user", payload.message)

        short_term = get_recent_messages(
            payload.user_id,
            session_id,
            limit=settings.SHORT_TERM_N + 1,
        )

        context_window = short_term
        if (
            context_window
            and context_window[-1]["role"] == "user"
            and context_window[-1]["content"] == payload.message
        ):
            context_window = context_window[:-1]

        session_summary_doc = get_latest_summary(payload.user_id, "session", session_id=session_id)
        lifetime_summary_doc = get_latest_summary(payload.user_id, "user")

        episodic = retrieve_relevant_episodes(
            payload.user_id,
            payload.message,
            top_k=settings.EPISODIC_TOP_K,
        )

        model_messages = build_chat_messages(
            user_message=payload.message,
            short_term_messages=context_window,
            lifetime_summary=(lifetime_summary_doc or {}).get("text"),
            session_summary=(session_summary_doc or {}).get("text"),
            episodic_facts=episodic,
        )

        reply = ollama_chat(settings.CHAT_MODEL, model_messages)
        save_message(payload.user_id, session_id, "assistant", reply)

        extracted_episodes = store_episodes_for_message(payload.user_id, session_id, payload.message)
        summary_updates = maybe_refresh_summaries(payload.user_id, session_id)

        return {
            "reply": reply,
            "memory_used": {
                "short_term_count": len(short_term),
                "short_term_messages": short_term,
                "long_term_used": {
                    "session_summary": (session_summary_doc or {}).get("text"),
                    "lifetime_summary": (lifetime_summary_doc or {}).get("text"),
                },
                "retrieved_episodic_facts": episodic,
                "newly_extracted_episodes": extracted_episodes,
                "summary_updates": summary_updates,
            },
        }
    except OllamaError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error during chat processing.")


@router.get("/memory/{user_id}", response_model=MemoryViewResponse)
def memory_view(user_id: str, session_id: str | None = None):
    try:
        sid = normalize_session_id(session_id)
        view = load_memory_view(user_id, sid)
        return view
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while fetching memory.")


@router.get("/aggregate/{user_id}", response_model=AggregateResponse)
def aggregate_view(user_id: str):
    try:
        return aggregate_user_activity(user_id)
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while aggregating memory.")
