"""
writer.py  —  Terminal 2
─────────────────────────
Agent 2 – Writer

Reads from the 'tasks' Kafka topic (question + plan from the Planner), uses
LangChain to write a short, clear answer, and publishes the draft to 'drafts'.

Usage:
    python writer.py
"""

import json

from kafka import KafkaConsumer, KafkaProducer
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

BOOTSTRAP_SERVERS = "localhost:9092"
TASKS_TOPIC = "tasks"
DRAFTS_TOPIC = "drafts"

SYSTEM_PROMPT = (
    "You are a Writer agent. Given a question and a step-by-step plan, write a "
    "clear, concise answer (3-5 sentences) that directly addresses the question "
    "by following the plan. Use plain language. Output only the answer text."
)


def write_answer(llm: ChatOllama, question: str, plan: str) -> str:
    user_content = (
        f"Question: {question}\n\n"
        f"Plan to follow:\n{plan}\n\n"
        "Write the answer now."
    )
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]
    return llm.invoke(messages).content.strip()


def main():
    llm = ChatOllama(
        model="llama3.2",
        temperature=0.5,
    )

    consumer = KafkaConsumer(
        TASKS_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="writer-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"[Writer] ✔ Listening on '{TASKS_TOPIC}'...")

    for msg in consumer:
        data = msg.value
        question = data.get("question", "")
        plan = data.get("plan", "")
        print(f"\n[Writer] ← Received task for: {question}")

        answer = write_answer(llm, question, plan)
        print(f"[Writer] Draft answer:\n{answer}")

        out = {"question": question, "plan": plan, "answer": answer}
        producer.send(DRAFTS_TOPIC, value=out)
        producer.flush()
        print(f"[Writer] → Sent draft to '{DRAFTS_TOPIC}'")


if __name__ == "__main__":
    main()
