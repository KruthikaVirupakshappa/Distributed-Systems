"""
planner.py  —  Terminal 1
──────────────────────────
Agent 1 – Planner

Reads questions from the 'inbox' Kafka topic, generates a numbered step-by-step
TODO plan using LangChain + OpenAI, and publishes the result to the 'tasks' topic.

Usage:
    python planner.py
"""

import json

from kafka import KafkaConsumer, KafkaProducer
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

BOOTSTRAP_SERVERS = "localhost:9092"
INBOX_TOPIC = "inbox"
TASKS_TOPIC = "tasks"

SYSTEM_PROMPT = (
    "You are a Planner agent. Given a question, produce a clear numbered "
    "step-by-step TODO plan (3-5 steps) that a writer can follow to answer it. "
    "Be concise. Output only the numbered list, nothing else."
)


def make_plan(llm: ChatOllama, question: str) -> str:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Question: {question}"),
    ]
    return llm.invoke(messages).content.strip()


def main():
    llm = ChatOllama(
        model="llama3.2",
        temperature=0.3,
    )

    consumer = KafkaConsumer(
        INBOX_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="planner-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"[Planner] ✔ Listening on '{INBOX_TOPIC}'...")

    for msg in consumer:
        data = msg.value
        question = data.get("question", "")
        print(f"\n[Planner] ← Received question: {question}")

        plan = make_plan(llm, question)
        print(f"[Planner] Generated plan:\n{plan}")

        out = {"question": question, "plan": plan}
        producer.send(TASKS_TOPIC, value=out)
        producer.flush()
        print(f"[Planner] → Sent plan to '{TASKS_TOPIC}'")


if __name__ == "__main__":
    main()
