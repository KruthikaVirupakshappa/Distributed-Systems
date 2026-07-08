"""
planner.py — Agent 1 (Planner)
Reads from 'inbox', generates a step-by-step plan, publishes to 'tasks'.
"""

import json
import uuid
import ollama
from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP_SERVERS = "localhost:29092"
INBOX_TOPIC = "inbox"
TASKS_TOPIC = "tasks"
MODEL = "llama3.2"

SYSTEM_PROMPT = (
    "You are a Planner agent. Given a question, produce a clear numbered "
    "step-by-step TODO plan (3-5 steps) that a writer can follow to answer it. "
    "Be concise. Output only the numbered list, nothing else."
)


def make_plan(question: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}"},
        ],
    )
    return response["message"]["content"].strip()


def main():
    consumer = KafkaConsumer(
        INBOX_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="hw10-planner-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"[Planner] Listening on '{INBOX_TOPIC}'...", flush=True)

    for msg in consumer:
        data = msg.value
        question = data.get("question", "")
        correlation_id = data.get("correlation_id", str(uuid.uuid4()))
        print(f"\n[Planner] [{correlation_id[:8]}] Received: {question}", flush=True)

        plan = make_plan(question)
        print(f"[Planner] Plan:\n{plan}", flush=True)

        producer.send(TASKS_TOPIC, value={"correlation_id": correlation_id, "question": question, "plan": plan})
        producer.flush()
        print(f"[Planner] → Sent plan to '{TASKS_TOPIC}'", flush=True)


if __name__ == "__main__":
    main()
