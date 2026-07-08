"""
reviewer.py  —  Terminal 3
───────────────────────────
Agent 3 – Reviewer

Reads draft answers from the 'drafts' Kafka topic, evaluates the answer using
LangChain, and publishes an approval message to the 'final' topic in the form:
    {"status": "approved", "answer": "...", "feedback": "..."}

Usage:
    python reviewer.py
"""

import json

from kafka import KafkaConsumer, KafkaProducer
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

BOOTSTRAP_SERVERS = "localhost:9092"
DRAFTS_TOPIC = "drafts"
FINAL_TOPIC = "final"

SYSTEM_PROMPT = (
    "You are a Reviewer agent. Evaluate the given answer for accuracy and clarity. "
    "Respond with ONLY a valid JSON object — no markdown, no code fences, no extra text:\n"
    '{"status": "approved", "answer": "<the answer verbatim>", "feedback": "<brief feedback>"}'
)


def review_answer(llm: ChatOllama, question: str, answer: str) -> dict:
    user_content = (
        f"Question: {question}\n\n"
        f"Answer to review:\n{answer}"
    )
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]
    raw = llm.invoke(messages).content.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "status": "approved",
            "answer": answer,
            "feedback": raw,
        }
    return result


def main():
    llm = ChatOllama(
        model="llama3.2",
        temperature=0.2,
    )

    consumer = KafkaConsumer(
        DRAFTS_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="reviewer-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"[Reviewer] ✔ Listening on '{DRAFTS_TOPIC}'...")

    for msg in consumer:
        data = msg.value
        question = data.get("question", "")
        answer = data.get("answer", "")
        print(f"\n[Reviewer] ← Received draft for: {question}")

        result = review_answer(llm, question, answer)
        print(f"[Reviewer] Approval result:\n{json.dumps(result, indent=2)}")

        producer.send(FINAL_TOPIC, value=result)
        producer.flush()
        print(f"[Reviewer] → Published to '{FINAL_TOPIC}' with status: {result.get('status')}")


if __name__ == "__main__":
    main()
