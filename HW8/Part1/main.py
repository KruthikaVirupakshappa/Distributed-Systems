import json
import logging
import threading
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from kafka import KafkaConsumer, KafkaProducer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [fastapi] %(message)s"
)
logger = logging.getLogger(__name__)

BOOTSTRAP_SERVERS = "localhost:9092"
REQUEST_TOPIC = "user_requests"
RESPONSE_TOPIC = "user_responses"
RESPONSE_TIMEOUT = 10  # seconds

# Pending responses keyed by correlation_id
_pending: dict[str, threading.Event] = {}
_results: dict[str, dict] = {}

producer: KafkaProducer = None


def response_listener():
    """Background thread: consume from user_responses and resolve pending requests."""
    consumer = KafkaConsumer(
        RESPONSE_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="fastapi-response-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=1000,
    )
    logger.info("Response listener started on topic: %s", RESPONSE_TOPIC)
    while not _shutdown_event.is_set():
        try:
            for message in consumer:
                msg = message.value
                cid = msg.get("correlation_id")
                logger.info(
                    "Response received from user_responses: correlation_id=%s", cid
                )
                if cid and cid in _pending:
                    _results[cid] = msg.get("data", {})
                    _pending[cid].set()
        except Exception:
            pass
    consumer.close()


_shutdown_event = threading.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    listener_thread = threading.Thread(target=response_listener, daemon=True)
    listener_thread.start()
    logger.info("FastAPI service started on http://127.0.0.1:8000")
    yield
    _shutdown_event.set()
    producer.close()


app = FastAPI(lifespan=lifespan)


def send_and_wait(data: dict) -> dict:
    correlation_id = str(uuid.uuid4())
    event = threading.Event()
    _pending[correlation_id] = event

    message = {
        "correlation_id": correlation_id,
        "reply_to": RESPONSE_TOPIC,
        "data": data,
    }

    logger.info(
        "Sending message to user_requests: correlation_id=%s operation=%s",
        correlation_id,
        data.get("operation"),
    )
    producer.send(REQUEST_TOPIC, value=message)
    producer.flush()

    if not event.wait(timeout=RESPONSE_TIMEOUT):
        _pending.pop(correlation_id, None)
        raise HTTPException(status_code=504, detail="Worker response timed out")

    _pending.pop(correlation_id, None)
    return _results.pop(correlation_id, {})


# ---------- Request models ----------

class CreateUserRequest(BaseModel):
    name: str
    email: str
    age: float


class GetUserRequest(BaseModel):
    userId: str


# ---------- Endpoints ----------

@app.post("/users")
def create_user(req: CreateUserRequest):
    result = send_and_wait({
        "operation": "CREATE_USER",
        "name": req.name,
        "email": req.email,
        "age": req.age,
    })
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@app.get("/users/{user_id}")
def get_user(user_id: str):
    result = send_and_wait({
        "operation": "GET_USER",
        "userId": user_id,
    })
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result
