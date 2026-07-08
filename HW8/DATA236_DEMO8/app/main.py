from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.kafka_rpc import KafkaRPC
import uuid

rpc = KafkaRPC()

direct_users = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rpc.start()
    yield
    await rpc.stop()


app = FastAPI(title="User CRUD Demo", lifespan=lifespan)


@app.get("/")
async def home():
    return {"message": "FastAPI service running"}


# Kafka-based endpoint
@app.post("/users")
async def handle_user_operation(payload: dict):
    response = await rpc.make_request(payload)
    return response


# Direct non-Kafka endpoint
@app.post("/users-direct")
async def handle_user_direct(payload: dict):
    operation = payload.get("operation")

    if operation == "CREATE_USER":
        if not payload.get("name"):
            return {"success": False, "message": "name is required"}
        if not payload.get("email"):
            return {"success": False, "message": "email is required"}
        if "age" not in payload or payload["age"] <= 0:
            return {"success": False, "message": "age must be greater than 0"}

        user_id = str(uuid.uuid4())
        direct_users[user_id] = {
            "userId": user_id,
            "name": payload["name"],
            "email": payload["email"],
            "age": payload["age"]
        }

        return {"success": True, "userId": user_id, "message": "User created directly"}

    elif operation == "GET_USER":
        user_id = payload.get("userId")
        if user_id not in direct_users:
            return {"success": False, "message": "User not found"}
        return {"success": True, "user": direct_users[user_id]}

    elif operation == "LIST_USERS":
        return {
            "success": True,
            "users": list(direct_users.values()),
            "count": len(direct_users)
        }

    return {"success": False, "message": "Invalid operation"}