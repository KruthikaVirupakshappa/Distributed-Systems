import os
import json
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient

from langchain_openai import ChatOpenAI

from langchain_classic.memory import ConversationSummaryBufferMemory
from langchain_classic.chains import ConversationChain

from langchain_core.prompts import PromptTemplate
from langchain_mongodb import MongoDBChatMessageHistory

# ── Config ──────────────────────────────────────────────────
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI      = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME        = os.getenv("MONGO_DB_NAME", "study_assistant")

if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY not found in .env!")

# ── Flask app ────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ── MongoDB client ───────────────────────────────────────────
mongo_client = MongoClient(MONGO_URI)
db           = mongo_client[DB_NAME]
profiles_col = db["student_profiles"]
sessions_col = db["chat_sessions"]

# ── LLM ─────────────────────────────────────────────────────
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=OPENAI_API_KEY)

extractor_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)




def load_profile(student_id: str) -> dict:
    doc = profiles_col.find_one({"student_id": student_id})
    if not doc:
        return {}
    doc.pop("_id", None)
    return doc


def save_profile(student_id: str, updates: dict):
    updates["updated_at"] = datetime.utcnow().isoformat()
    profiles_col.update_one(
        {"student_id": student_id},
        {"$set": updates},
        upsert=True,
    )


def ensure_profile(student_id: str, name: str) -> dict:
    profile = load_profile(student_id)
    if not profile:
        now = datetime.utcnow().isoformat()
        profile = {
            "student_id":      student_id,
            "name":            name,
            "topics_studied":  [],
            "difficult_areas": [],
            "learning_goals":  [],
            "session_count":   0,
            "created_at":      now,
            "last_seen":       now,
        }
        profiles_col.insert_one({**profile})
    return profile


def format_profile_for_prompt(profile: dict) -> str:
    if not profile:
        return "No prior history — this is the student's first session."
    topics = ", ".join(profile.get("topics_studied",  [])) or "None yet"
    hard   = ", ".join(profile.get("difficult_areas", [])) or "None identified"
    goals  = ", ".join(profile.get("learning_goals",  [])) or "None set"
    return (
        f"Student Name    : {profile.get('name', 'Student')}\n"
        f"Sessions So Far : {profile.get('session_count', 0)}\n"
        f"Last Seen       : {profile.get('last_seen', 'N/A')}\n"
        f"Topics Studied  : {topics}\n"
        f"Difficult Areas : {hard}\n"
        f"Learning Goals  : {goals}"
    )




def extract_and_save_memory(student_id: str, user_msg: str, ai_response: str) -> dict:
    """
    Uses a second zero-temperature LLM call to extract structured
    learning data from the conversation, then persists it to MongoDB.
    Returns a dict of what was newly saved.
    """
    extraction_prompt = f"""You are a memory extraction assistant for a study app.
Analyze ONLY the student's message below and extract structured learning data.

Student message: "{user_msg}"
AI response (for context only): "{ai_response}"

Return ONLY a valid JSON object with these exact keys (empty list if nothing found):
{{
  "topics_studied":  ["specific subjects or topics the student said they are studying or learning"],
  "difficult_areas": ["topics the student explicitly said they struggle with or find hard"],
  "learning_goals":  ["explicit goals or targets the student mentioned wanting to achieve"]
}}

Rules:
- Extract from the STUDENT message only, not from what the AI said
- Be specific: "Linked Lists" not "programming"
- Normalize capitalization: "DSA", "Linked Lists", "sorting algorithms"
- Return [] for any field with nothing to extract
- Return ONLY raw JSON — no markdown, no code fences, no explanation"""

    try:
        result = extractor_llm.invoke(extraction_prompt)
        raw    = result.content.strip()

        # Strip markdown fences if model adds them anyway
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        extracted = json.loads(raw)

        profile        = load_profile(student_id)
        updated_fields = {}

        for field in ("topics_studied", "difficult_areas", "learning_goals"):
            new_items = extracted.get(field, [])
            if not new_items:
                continue
            current  = profile.get(field, [])
            combined = list(current)
            added    = False
            for item in new_items:
                item = item.strip()
                if item and item not in combined:
                    combined.append(item)
                    added = True
            if added:
                updated_fields[field] = combined

        if updated_fields:
            save_profile(student_id, updated_fields)
            print(f"[memory] Saved for {student_id}: {updated_fields}")
            # Rebuild chain so the next prompt includes the updated profile
            _chain_cache.pop(student_id, None)
            get_chain(student_id, load_profile(student_id))

        return updated_fields

    except Exception as e:
        print(f"[memory extraction error] {e}")
        return {}




_chain_cache: dict = {}


def get_chain(student_id: str, profile: dict) -> ConversationChain:
    if student_id in _chain_cache:
        return _chain_cache[student_id]

    # MongoDBChatMessageHistory — persists every message in MongoDB
    chat_history = MongoDBChatMessageHistory(
        connection_string=MONGO_URI,
        session_id=student_id,
        database_name=DB_NAME,
        collection_name="chat_messages",
    )

    # SummaryBufferMemory: keeps recent messages verbatim,
    # auto-summarises older ones to save tokens
    memory = ConversationSummaryBufferMemory(
        llm=llm,
        max_token_limit=800,
        chat_memory=chat_history,
        return_messages=True,
        memory_key="history",
    )

    profile_summary = format_profile_for_prompt(profile)

    template = f"""You are an expert, encouraging AI study tutor with a perfect memory of your student.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STUDENT LONG-TERM PROFILE (persisted across ALL sessions in MongoDB):
{profile_summary}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your behaviour:
• Reference the student's past topics to connect new knowledge
• Pay extra attention to their difficult areas
• Help them progress toward their stated goals
• Keep a warm, clear, encouraging tone
• Format responses in clear paragraphs

Current conversation:
{{history}}
Student: {{input}}
Tutor:"""

    prompt = PromptTemplate(input_variables=["history", "input"], template=template)
    chain  = ConversationChain(llm=llm, memory=memory, prompt=prompt, verbose=False)

    _chain_cache[student_id] = chain
    return chain


# ═══════════════════════════════════════════════════════════
#  API ROUTES
# ═══════════════════════════════════════════════════════════

@app.route("/api/session/start", methods=["POST"])
def start_session():
    data       = request.json or {}
    name       = data.get("name", "Student").strip()
    student_id = name.lower().replace(" ", "_")

    profile  = ensure_profile(student_id, name)
    is_new   = profile.get("session_count", 0) == 0

    new_count = profile.get("session_count", 0) + 1
    save_profile(student_id, {
        "session_count": new_count,
        "last_seen":     datetime.utcnow().isoformat(),
    })
    profile = load_profile(student_id)

    get_chain(student_id, profile)

    return jsonify({
        "student_id":    student_id,
        "name":          profile["name"],
        "is_new":        is_new,
        "session_count": new_count,
        "last_seen":     profile.get("last_seen", ""),
        "profile":       profile,
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    data       = request.json or {}
    student_id = data.get("student_id", "")
    user_msg   = data.get("message", "").strip()

    if not student_id or not user_msg:
        return jsonify({"error": "student_id and message required"}), 400

    profile = load_profile(student_id)
    if not profile:
        return jsonify({"error": "Session not found. Call /api/session/start first."}), 404

    chain = get_chain(student_id, profile)

    try:
        response = chain.predict(input=user_msg)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # ── Auto-extract topics / goals / difficulty → save to MongoDB ──
    saved = extract_and_save_memory(student_id, user_msg, response)

    sessions_col.update_one(
        {"student_id": student_id},
        {"$push": {"messages": {
            "role":      "user",
            "content":   user_msg,
            "timestamp": datetime.utcnow().isoformat(),
        }}},
        upsert=True,
    )

    # Return memory_saved so the frontend can refresh the sidebar immediately
    return jsonify({"response": response, "memory_saved": saved})


@app.route("/api/profile", methods=["GET"])
def get_profile():
    student_id = request.args.get("student_id", "")
    if not student_id:
        return jsonify({"error": "student_id required"}), 400
    profile = load_profile(student_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(profile)


@app.route("/api/profile/update", methods=["POST"])
def update_profile():
    data       = request.json or {}
    student_id = data.get("student_id", "")
    field      = data.get("field", "")
    value      = data.get("value", "").strip()

    allowed = {"topics_studied", "difficult_areas", "learning_goals"}
    if field not in allowed:
        return jsonify({"error": f"field must be one of {allowed}"}), 400

    profile = load_profile(student_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    current = profile.get(field, [])
    if value and value not in current:
        current.append(value)
        save_profile(student_id, {field: current})

    _chain_cache.pop(student_id, None)
    profile = load_profile(student_id)
    get_chain(student_id, profile)

    return jsonify({"success": True, "updated": field, "values": current})


@app.route("/api/history", methods=["GET"])
def get_history():
    student_id = request.args.get("student_id", "")
    if not student_id:
        return jsonify({"error": "student_id required"}), 400

    history_store = MongoDBChatMessageHistory(
        connection_string=MONGO_URI,
        session_id=student_id,
        database_name=DB_NAME,
        collection_name="chat_messages",
    )

    messages = []
    for msg in history_store.messages:
        messages.append({
            "role":    "user" if msg.type == "human" else "assistant",
            "content": msg.content,
        })

    return jsonify({"messages": messages})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "db": DB_NAME})


# ── Run ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n   Study Assistant API running on http://localhost:5000")
    print(f"   MongoDB: {MONGO_URI}")
    print("  Open index.html in your browser\n")
    app.run(debug=True, port=5000)
