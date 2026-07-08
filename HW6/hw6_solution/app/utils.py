import math
from datetime import datetime, timezone

from bson import ObjectId


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def is_valid_object_id(value: str) -> bool:
    try:
        ObjectId(value)
        return True
    except Exception:
        return False


def to_object_id(value: str) -> ObjectId:
    return ObjectId(value)


def serialize_task(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "title": doc.get("title"),
        "description": doc.get("description"),
        "status": doc.get("status"),
        "priority": doc.get("priority"),
        "dueDate": doc.get("dueDate"),
        "category": doc.get("category"),
        "createdAt": doc.get("createdAt"),
        "updatedAt": doc.get("updatedAt"),
    }


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))

    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0

    return dot / (mag_a * mag_b)
