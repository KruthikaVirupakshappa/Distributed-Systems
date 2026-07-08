import json
import re
import uuid
import logging
from kafka import KafkaConsumer, KafkaProducer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [worker] %(message)s"
)
logger = logging.getLogger(__name__)

BOOTSTRAP_SERVERS = "localhost:9092"
REQUEST_TOPIC = "user_requests"

# In-memory user store
users: dict[str, dict] = {}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_create_user(data: dict) -> str | None:
    """Return error message if invalid, else None."""
    if not data.get("name"):
        return "name is required"
    if not data.get("email") or not EMAIL_RE.match(data["email"]):
        return "valid email is required"
    age = data.get("age")
    if age is None:
        return "age is required"
    if not isinstance(age, (int, float)) or age <= 0:
        return "age must be a positive number"
    return None


def handle_create_user(data: dict) -> dict:
    error = validate_create_user(data)
    if error:
        return {"success": False, "message": error}

    user_id = str(uuid.uuid4())
    users[user_id] = {
        "userId": user_id,
        "name": data["name"],
        "email": data["email"],
        "age": data["age"],
    }
    logger.info("Created user: userId=%s name=%s", user_id, data["name"])
    return {"success": True, "userId": user_id, "message": "User created"}


def handle_get_user(data: dict) -> dict:
    user_id = data.get("userId")
    if not user_id:
        return {"success": False, "message": "userId is required"}
    user = users.get(user_id)
    if not user:
        return {"success": False, "message": f"User {user_id} not found"}
    logger.info("Retrieved user: userId=%s", user_id)
    return {"success": True, "user": user}


def process_message(msg: dict) -> dict:
    correlation_id = msg.get("correlation_id")
    reply_to = msg.get("reply_to", "user_responses")
    data = msg.get("data", {})
    operation = data.get("operation")

    logger.info(
        "Processing message: correlation_id=%s operation=%s",
        correlation_id,
        operation,
    )

    if operation == "CREATE_USER":
        result = handle_create_user(data)
    elif operation == "GET_USER":
        result = handle_get_user(data)
    else:
        result = {"success": False, "message": f"Unknown operation: {operation}"}

    return {
        "correlation_id": correlation_id,
        "data": result,
    }, reply_to


def main():
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    consumer = KafkaConsumer(
        REQUEST_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="user-worker-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    logger.info("Consumer is ready and listening on topic: %s", REQUEST_TOPIC)

    for message in consumer:
        try:
            msg = message.value
            logger.info("Message received from user_requests: %s", json.dumps(msg))

            response, reply_to = process_message(msg)

            producer.send(reply_to, value=response)
            producer.flush()
            logger.info(
                "Response sent to %s: %s", reply_to, json.dumps(response)
            )
        except Exception as exc:
            logger.error("Error processing message: %s", exc)


if __name__ == "__main__":
    main()
