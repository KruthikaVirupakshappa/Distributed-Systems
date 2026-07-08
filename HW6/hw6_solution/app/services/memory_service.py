import json
import re

from ..config import settings
from ..db import (
    get_episodes_collection,
    get_messages_collection,
    get_summaries_collection,
)
from ..utils import cosine_similarity, now_utc
from .ollama_service import OllamaError, chat as ollama_chat, embed as ollama_embed


def normalize_session_id(session_id: str | None) -> str:
    if session_id and session_id.strip():
        return session_id.strip()
    return settings.DEFAULT_SESSION_ID


def save_message(user_id: str, session_id: str, role: str, content: str) -> dict:
    doc = {
        "user_id": user_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": now_utc(),
    }
    get_messages_collection().insert_one(doc)
    return doc


def get_recent_messages(user_id: str, session_id: str, limit: int) -> list[dict]:
    docs = list(
        get_messages_collection()
        .find({"user_id": user_id, "session_id": session_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    docs.reverse()

    return [
        {
            "role": d.get("role", "user"),
            "content": d.get("content", ""),
            "created_at": d.get("created_at"),
        }
        for d in docs
    ]


def get_latest_summary(user_id: str, scope: str, session_id: str | None = None) -> dict | None:
    query = {"user_id": user_id, "scope": scope}
    if scope == "session":
        query["session_id"] = session_id
    else:
        query["session_id"] = None

    return get_summaries_collection().find_one(query, sort=[("created_at", -1)])


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9]*", "", cleaned)
        cleaned = cleaned.rstrip("`").strip()
    return cleaned


def _try_parse_json(raw_text: str):
    cleaned = _strip_code_fences(raw_text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[[\s\S]*\]", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    return None


def _fallback_fact_extraction(message: str) -> list[dict]:
    parts = [p.strip() for p in re.split(r"[.!?]\s+", message) if p.strip()]
    facts = []

    for part in parts:
        if len(part) < 8:
            continue
        facts.append({"fact": part[:180], "importance": 0.5})
        if len(facts) == 3:
            break

    if not facts and message.strip():
        facts.append({"fact": message.strip()[:180], "importance": 0.5})

    return facts


def extract_episode_candidates(message: str) -> list[dict]:
    system_prompt = (
        "Extract up to 3 useful user facts for future conversation memory. "
        "Return JSON array only. Each item must have keys: fact (string) and importance (float 0..1)."
    )

    user_prompt = (
        f"User message: {message}\n\n"
        "Rules:\n"
        "- Keep facts short and concrete.\n"
        "- Skip generic chatter.\n"
        "- importance should be 0.0 to 1.0.\n"
        "- Return only JSON array."
    )

    raw = ollama_chat(
        settings.CHAT_MODEL,
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )

    parsed = _try_parse_json(raw)
    if not isinstance(parsed, list):
        return _fallback_fact_extraction(message)

    facts = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        fact = str(item.get("fact", "")).strip()
        if not fact:
            continue

        try:
            importance = float(item.get("importance", 0.5))
        except (TypeError, ValueError):
            importance = 0.5

        importance = max(0.0, min(1.0, importance))
        facts.append({"fact": fact[:220], "importance": importance})

        if len(facts) == 3:
            break

    return facts or _fallback_fact_extraction(message)


def store_episodes_for_message(user_id: str, session_id: str, message: str) -> list[dict]:
    episodes_col = get_episodes_collection()
    facts = extract_episode_candidates(message)
    inserted = []

    for fact_obj in facts:
        emb = ollama_embed(fact_obj["fact"])
        doc = {
            "user_id": user_id,
            "session_id": session_id,
            "fact": fact_obj["fact"],
            "importance": fact_obj["importance"],
            "embedding": emb,
            "created_at": now_utc(),
        }
        episodes_col.insert_one(doc)
        inserted.append({
            "fact": doc["fact"],
            "importance": doc["importance"],
        })

    return inserted


def retrieve_relevant_episodes(user_id: str, message: str, top_k: int) -> list[dict]:
    query_vec = ollama_embed(message)
    candidates = list(
        get_episodes_collection()
        .find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(250)
    )

    scored = []
    for item in candidates:
        emb = item.get("embedding")
        if not isinstance(emb, list):
            continue

        try:
            emb = [float(v) for v in emb]
        except (TypeError, ValueError):
            continue

        sim = cosine_similarity(query_vec, emb)
        if sim <= 0.0:
            continue

        scored.append(
            {
                "fact": item.get("fact", ""),
                "importance": float(item.get("importance", 0.0)),
                "similarity": round(sim, 4),
                "created_at": item.get("created_at"),
            }
        )

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


def build_chat_messages(
    user_message: str,
    short_term_messages: list[dict],
    lifetime_summary: str | None,
    session_summary: str | None,
    episodic_facts: list[dict],
) -> list[dict]:
    episodic_line = "; ".join(
        f"{e['fact']} (imp={e['importance']:.2f}, sim={e['similarity']:.2f})"
        for e in episodic_facts
    )
    if not episodic_line:
        episodic_line = "None"

    system_context = (
        "You are a concise and helpful assistant. Use memory context when useful, "
        "but do not hallucinate details that are not present.\n\n"
        f"Lifetime summary:\n{lifetime_summary or 'None'}\n\n"
        f"Session summary:\n{session_summary or 'None'}\n\n"
        f"Top episodic facts:\n{episodic_line}"
    )

    messages = [{"role": "system", "content": system_context}]
    messages.extend(
        {"role": m["role"], "content": m["content"]}
        for m in short_term_messages
    )
    messages.append({"role": "user", "content": user_message})
    return messages


def _conversation_to_text(messages: list[dict]) -> str:
    return "\n".join(f"{m['role']}: {m['content']}" for m in messages)


def maybe_refresh_summaries(user_id: str, session_id: str) -> dict | None:
    msg_col = get_messages_collection()
    user_count = msg_col.count_documents(
        {"user_id": user_id, "session_id": session_id, "role": "user"}
    )

    every_n = max(1, settings.SUMMARIZE_EVERY_USER_MSGS)
    if user_count == 0 or user_count % every_n != 0:
        return None

    recent_messages = get_recent_messages(user_id, session_id, limit=28)
    if not recent_messages:
        return None

    summary_prompt = (
        "Summarize this conversation into concise bullets. Include user goals, "
        "preferences, and unresolved tasks. Keep under 8 bullets."
    )
    convo_text = _conversation_to_text(recent_messages)

    session_summary_text = ollama_chat(
        settings.CHAT_MODEL,
        [
            {"role": "system", "content": summary_prompt},
            {"role": "user", "content": convo_text},
        ],
        temperature=0.1,
    )

    summaries_col = get_summaries_collection()
    summaries_col.update_one(
        {"user_id": user_id, "session_id": session_id, "scope": "session"},
        {
            "$set": {
                "text": session_summary_text,
                "created_at": now_utc(),
            }
        },
        upsert=True,
    )

    lifetime_summary_text = refresh_lifetime_summary(user_id)

    return {
        "session_summary": session_summary_text,
        "lifetime_summary": lifetime_summary_text,
    }


def refresh_lifetime_summary(user_id: str) -> str:
    summaries_col = get_summaries_collection()
    session_summaries = list(
        summaries_col.find({"user_id": user_id, "scope": "session"})
        .sort("created_at", -1)
        .limit(8)
    )

    if not session_summaries:
        return ""

    joined = "\n\n".join(
        f"Session summary {idx + 1}: {s.get('text', '')}"
        for idx, s in enumerate(session_summaries)
    )

    lifetime_prompt = (
        "Create a compact long-term user profile summary from session summaries. "
        "Focus on durable preferences, goals, and recurring patterns. Keep it concise."
    )

    lifetime_summary_text = ollama_chat(
        settings.CHAT_MODEL,
        [
            {"role": "system", "content": lifetime_prompt},
            {"role": "user", "content": joined},
        ],
        temperature=0.1,
    )

    summaries_col.update_one(
        {"user_id": user_id, "scope": "user", "session_id": None},
        {
            "$set": {
                "text": lifetime_summary_text,
                "created_at": now_utc(),
            }
        },
        upsert=True,
    )

    return lifetime_summary_text


def load_memory_view(user_id: str, session_id: str) -> dict:
    session_summary = get_latest_summary(user_id, "session", session_id=session_id)
    lifetime_summary = get_latest_summary(user_id, "user")

    episodes = list(
        get_episodes_collection()
        .find({"user_id": user_id, "session_id": session_id})
        .sort("created_at", -1)
        .limit(20)
    )

    return {
        "user_id": user_id,
        "session_id": session_id,
        "recent_messages": get_recent_messages(user_id, session_id, limit=16),
        "latest_session_summary": session_summary,
        "latest_lifetime_summary": lifetime_summary,
        "recent_episodes": [
            {
                "fact": e.get("fact", ""),
                "importance": float(e.get("importance", 0.0)),
                "created_at": e.get("created_at"),
            }
            for e in episodes
        ],
    }


def aggregate_user_activity(user_id: str) -> dict:
    msg_col = get_messages_collection()
    summaries_col = get_summaries_collection()

    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$created_at",
                    }
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    daily = [
        {"date": row["_id"], "count": row["count"]}
        for row in msg_col.aggregate(pipeline)
    ]

    summaries = list(
        summaries_col.find({"user_id": user_id}).sort("created_at", -1).limit(6)
    )

    return {
        "user_id": user_id,
        "daily_message_counts": daily,
        "recent_summaries": [
            {
                "user_id": s.get("user_id"),
                "session_id": s.get("session_id"),
                "scope": s.get("scope"),
                "text": s.get("text"),
                "created_at": s.get("created_at"),
            }
            for s in summaries
        ],
    }
