from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, OperationFailure
from .config import settings

_client = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI)
    return _client


def get_db():
    return get_client()[settings.MONGODB_DB]


def get_tasks_collection():
    return get_db()["tasks"]


def get_messages_collection():
    return get_db()["messages"]


def get_summaries_collection():
    return get_db()["summaries"]


def get_episodes_collection():
    return get_db()["episodes"]


def ensure_collections() -> None:
    db = get_db()

    tasks_schema = {
        "bsonType": "object",
        "required": ["title", "status", "priority", "dueDate", "category", "createdAt", "updatedAt"],
        "properties": {
            "title": {"bsonType": "string", "maxLength": 100},
            "description": {"bsonType": ["string", "null"]},
            "status": {"enum": ["pending", "in-progress", "completed"]},
            "priority": {"enum": ["low", "medium", "high"]},
            "dueDate": {"bsonType": "date"},
            "category": {"enum": ["Work", "Personal", "Shopping", "Health", "Other"]},
            "createdAt": {"bsonType": "date"},
            "updatedAt": {"bsonType": "date"},
        },
    }

    if "tasks" not in db.list_collection_names():
        try:
            db.create_collection(
                "tasks",
                validator={"$jsonSchema": tasks_schema},
                validationLevel="strict",
            )
        except CollectionInvalid:
            pass
    else:
        try:
            db.command(
                {
                    "collMod": "tasks",
                    "validator": {"$jsonSchema": tasks_schema},
                    "validationLevel": "moderate",
                }
            )
        except OperationFailure:
            # Non-admin users may not be allowed to modify validator; app-level
            # Pydantic validation still enforces constraints.
            pass

    get_tasks_collection().create_index("createdAt")
    get_tasks_collection().create_index("dueDate")

    get_messages_collection().create_index([("user_id", 1), ("session_id", 1), ("created_at", -1)])
    get_messages_collection().create_index([("user_id", 1), ("created_at", -1)])

    get_summaries_collection().create_index([("user_id", 1), ("scope", 1), ("session_id", 1), ("created_at", -1)])

    get_episodes_collection().create_index([("user_id", 1), ("created_at", -1)])
    get_episodes_collection().create_index([("user_id", 1), ("session_id", 1), ("created_at", -1)])
