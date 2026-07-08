"""
send_question.py — kick off the pipeline with a question.
Usage:
    python send_question.py
    python send_question.py "What is the CAP theorem?"
"""

import json
import sys
import uuid

from kafka import KafkaProducer

BOOTSTRAP_SERVERS = "localhost:29092"
INBOX_TOPIC = "inbox"


def main():
    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "What is distributed computing and why is it important?"
    )
    correlation_id = str(uuid.uuid4())

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    message = {"correlation_id": correlation_id, "question": question}
    producer.send(INBOX_TOPIC, value=message)
    producer.flush()
    producer.close()

    print(f"[send_question] Sent to '{INBOX_TOPIC}'")
    print(f"  correlation_id : {correlation_id}")
    print(f"  question       : {question}")


if __name__ == "__main__":
    main()
