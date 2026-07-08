from bson import ObjectId
from datetime import datetime, timezone

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

def serialize_session(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "topic": doc.get("topic"),
        "notes": doc.get("notes"),
        "status": doc.get("status"),
        "intensity": doc.get("intensity"),
        "scheduledFor": doc.get("scheduledFor"),
        "subject": doc.get("subject"),
        "createdAt": doc.get("createdAt"),
        "updatedAt": doc.get("updatedAt"),
    }