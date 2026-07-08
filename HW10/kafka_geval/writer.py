"""
writer.py — Agent 2 (Writer)
Reads from 'tasks', writes a draft answer, publishes to 'drafts'.
"""

import json
import ollama
from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP_SERVERS = "localhost:29092"
TASKS_TOPIC = "tasks"
DRAFTS_TOPIC = "drafts"
MODEL = "llama3.2"

SYSTEM_PROMPT = (
    "You are a Writer agent. Given a question and a step-by-step plan, write a "
    "clear, concise answer (3-5 sentences) that directly addresses the question "
    "by following the plan. Use plain language. Output only the answer text."
)


def write_answer(question: str, plan: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}\n\nPlan:\n{plan}\n\nWrite the answer now."},
        ],
    )
    return response["message"]["content"].strip()


def main():
    consumer = KafkaConsumer(
        TASKS_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="hw10-writer-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"[Writer] Listening on '{TASKS_TOPIC}'...", flush=True)

    for msg in consumer:
        data = msg.value
        question = data.get("question", "")
        plan = data.get("plan", "")
        correlation_id = data.get("correlation_id", "")
        print(f"\n[Writer] [{correlation_id[:8]}] Received task for: {question}", flush=True)

        draft = write_answer(question, plan)
        print(f"[Writer] Draft:\n{draft}", flush=True)

        producer.send(DRAFTS_TOPIC, value={
            "correlation_id": correlation_id,
            "question": question,
            "plan": plan,
            "draft": draft,
        })
        producer.flush()
        print(f"[Writer] → Sent draft to '{DRAFTS_TOPIC}'", flush=True)


if __name__ == "__main__":
    main()
