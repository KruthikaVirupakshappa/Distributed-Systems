"""
send_question.py  —  Terminal 4
────────────────────────────────
Sends a question to the 'inbox' Kafka topic to kick off the 3-agent pipeline.

Usage:
    python send_question.py
    python send_question.py "What is the CAP theorem?"
"""

import json
import sys

from kafka import KafkaProducer

BOOTSTRAP_SERVERS = "localhost:9092"
INBOX_TOPIC = "inbox"


def main():
    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "What is distributed computing and why is it important?"
    )

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    message = {"question": question}
    producer.send(INBOX_TOPIC, value=message)
    producer.flush()
    producer.close()

    print(f"[send_question] ✔ Sent to '{INBOX_TOPIC}': {message}")


if __name__ == "__main__":
    main()
