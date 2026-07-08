import asyncio
import json
import uuid
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
REQUEST_TOPIC = "book_requests"
RESPONSE_TOPIC = "book_responses"
TIMEOUT_SECONDS = 8


class KafkaRPC:
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS
        )

        self.consumer = AIOKafkaConsumer(
            RESPONSE_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="fastapi-response-group",
            auto_offset_reset="earliest",
            enable_auto_commit=True
        )

        self.pending = {}
        self.consumer_task = None

    async def start(self):
        await self.producer.start()
        await self.consumer.start()
        self.consumer_task = asyncio.create_task(self.consume_responses())
        print("FastAPI KafkaRPC started")
        print(f"Listening for Kafka responses on topic: {RESPONSE_TOPIC}")

    async def stop(self):
        if self.consumer_task:
            self.consumer_task.cancel()
            try:
                await self.consumer_task
            except asyncio.CancelledError:
                pass

        await self.consumer.stop()
        await self.producer.stop()
        print("FastAPI KafkaRPC stopped")

    async def consume_responses(self):
        async for msg in self.consumer:
            data = json.loads(msg.value.decode())
            correlation_id = data.get("correlation_id")

            print("\n[FASTAPI] Received message from RESPONSE topic")
            print(f"[FASTAPI] Topic={msg.topic}, Partition={msg.partition}, Offset={msg.offset}")
            print(f"[FASTAPI] Message value={json.dumps(data, indent=2)}")

            if correlation_id in self.pending:
                future = self.pending.pop(correlation_id)
                print(f"[FASTAPI] Matched correlation_id: {correlation_id}")
                print(f"[FASTAPI] Pending requests left: {list(self.pending.keys())}")
                if not future.done():
                    future.set_result(data.get("data"))
            else:
                print(f"[FASTAPI] No pending request found for correlation_id: {correlation_id}")

    async def make_request(self, payload: dict):
        correlation_id = str(uuid.uuid4())

        message = {
            "correlation_id": correlation_id,
            "reply_to": RESPONSE_TOPIC,
            "data": payload
        }

        future = asyncio.get_event_loop().create_future()
        self.pending[correlation_id] = future

        print("\n[FASTAPI] Sending message to REQUEST topic")
        print(f"[FASTAPI] correlation_id={correlation_id}")
        print(f"[FASTAPI] reply_to={RESPONSE_TOPIC}")
        print(f"[FASTAPI] Pending requests now: {list(self.pending.keys())}")
        print(f"[FASTAPI] Message value={json.dumps(message, indent=2)}")

        metadata = await self.producer.send_and_wait(
            REQUEST_TOPIC,
            json.dumps(message).encode()
        )

        print(
            f"[FASTAPI] Sent to topic={metadata.topic}, "
            f"partition={metadata.partition}, offset={metadata.offset}"
        )

        try:
            response = await asyncio.wait_for(future, timeout=TIMEOUT_SECONDS)
            print(f"[FASTAPI] Final response matched for correlation_id={correlation_id}")
            print(f"[FASTAPI] Returning HTTP response to client: {response}")
            return response
        except asyncio.TimeoutError:
            self.pending.pop(correlation_id, None)
            return {
                "success": False,
                "message": f"Timeout for correlation_id {correlation_id}"
            }