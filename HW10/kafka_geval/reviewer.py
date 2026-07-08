"""
reviewer.py — Agent 3 (Reviewer)
Reads from 'drafts', reviews and potentially improves the answer,
publishes approved result to 'final'.
"""

import json
import ollama
from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP_SERVERS = "localhost:29092"
DRAFTS_TOPIC = "drafts"
FINAL_TOPIC = "final"
MODEL = "llama3.2"

SYSTEM_PROMPT = (
    "You are a Reviewer agent. Evaluate the given answer for accuracy and clarity. "
    "If needed, improve it slightly. "
    "Respond with ONLY a valid JSON object — no markdown, no code fences, no extra text:\n"
    '{"status": "approved", "answer": "<final answer>", "feedback": "<brief feedback>"}'
)


def review_answer(question: str, draft: str) -> dict:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}\n\nAnswer to review:\n{draft}"},
        ],
    )
    raw = response["message"]["content"].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"status": "approved", "answer": draft, "feedback": raw}


def main():
    consumer = KafkaConsumer(
        DRAFTS_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="hw10-reviewer-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"[Reviewer] Listening on '{DRAFTS_TOPIC}'...", flush=True)

    for msg in consumer:
        data = msg.value
        question = data.get("question", "")
        draft = data.get("draft", "")
        plan = data.get("plan", "")
        correlation_id = data.get("correlation_id", "")
        print(f"\n[Reviewer] [{correlation_id[:8]}] Received draft for: {question}", flush=True)

        result = review_answer(question, draft)
        print(f"[Reviewer] Review:\n{json.dumps(result, indent=2)}", flush=True)

        producer.send(FINAL_TOPIC, value={
            "correlation_id": correlation_id,
            "question": question,
            "plan": plan,
            "draft": draft,
            "final_answer": result.get("answer", draft),
            "feedback": result.get("feedback", ""),
            "status": result.get("status", "approved"),
        })
        producer.flush()
        print(f"[Reviewer] → Published to '{FINAL_TOPIC}'", flush=True)


if __name__ == "__main__":
    main()
