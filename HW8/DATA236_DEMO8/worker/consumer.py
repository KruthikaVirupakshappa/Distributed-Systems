import asyncio
import json
import uuid
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
REQUEST_TOPIC = "book_requests"

books = {}


def validate_create(data):
    if not data.get("title"):
        return "title is required"
    if not data.get("author"):
        return "author is required"
    if "price" not in data:
        return "price is required"
    if not isinstance(data.get("price"), (int, float)) or data.get("price") <= 0:
        return "price must be greater than 0"
    return None


def process_request(req):
    operation = req.get("operation")

    if operation == "CREATE_BOOK":
        error = validate_create(req)
        if error:
            return {"success": False, "message": error}

        book_id = str(uuid.uuid4())
        books[book_id] = {
            "bookId": book_id,
            "title": req["title"],
            "author": req["author"],
            "price": req["price"]
        }

        return {
            "success": True,
            "bookId": book_id,
            "message": "Book created"
        }

    elif operation == "GET_BOOK":
        book_id = req.get("bookId")
        if book_id not in books:
            return {"success": False, "message": "Book not found"}

        return {
            "success": True,
            "book": books[book_id]
        }

    elif operation == "UPDATE_BOOK":
        book_id = req.get("bookId")
        updates = req.get("updates", {})

        if book_id not in books:
            return {"success": False, "message": "Book not found"}

        if "price" in updates:
            if not isinstance(updates["price"], (int, float)) or updates["price"] <= 0:
                return {"success": False, "message": "price must be greater than 0"}

        books[book_id].update(updates)

        return {
            "success": True,
            "book": books[book_id]
        }

    elif operation == "DELETE_BOOK":
        book_id = req.get("bookId")

        if book_id not in books:
            return {"success": False, "message": "Book not found"}

        del books[book_id]

        return {
            "success": True,
            "message": "Book deleted"
        }

    elif operation == "LIST_BOOKS":
        return {
            "success": True,
            "books": list(books.values()),
            "count": len(books)
        }

    else:
        return {
            "success": False,
            "message": "Invalid operation"
        }


async def main():
    consumer = AIOKafkaConsumer(
        REQUEST_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="book-worker-group",
        auto_offset_reset="earliest",
        enable_auto_commit=True
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS
    )

    await consumer.start()
    await producer.start()

    print("Consumer is ready and listening...")

    try:
        async for msg in consumer:
            payload = json.loads(msg.value.decode())

            correlation_id = payload.get("correlation_id")
            reply_to = payload.get("reply_to")
            data = payload.get("data")

            print("\n[WORKER] Received message from REQUEST topic")
            print(f"[WORKER] Topic={msg.topic}, Partition={msg.partition}, Offset={msg.offset}")
            print(f"[WORKER] Full request message={json.dumps(payload, indent=2)}")
            print(f"[WORKER] correlation_id={correlation_id}")
            print(f"[WORKER] reply_to={reply_to}")
            print(f"[WORKER] actual business payload={json.dumps(data, indent=2)}")

            result = process_request(data)

            response = {
                "correlation_id": correlation_id,
                "data": result
            }

            print("[WORKER] Sending message to RESPONSE topic")
            print(f"[WORKER] Response message={json.dumps(response, indent=2)}")

            metadata = await producer.send_and_wait(
                reply_to,
                json.dumps(response).encode()
            )

            print(
                f"[WORKER] Sent to topic={metadata.topic}, "
                f"partition={metadata.partition}, offset={metadata.offset}"
            )

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())