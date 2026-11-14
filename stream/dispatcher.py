
import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

import pika

AMQP_URL = os.environ.get("AMQP_URL")

if not AMQP_URL:
    raise RuntimeError("Please set the AMQP_URL environment variable first.")

connection = pika.BlockingConnection(
    pika.URLParameters(AMQP_URL)
)
channel = connection.channel()

channel.exchange_declare(
    exchange="rapido-dispatch",
    exchange_type="topic",
    durable=True
)

zones = {
    "bangalore": ["koramangala", "indiranagar", "whitefield"],
    "chennai": ["tnagar", "whitefield"]
}

message_count = 0

try:
    while True:
        message_count += 1

        city = random.choice(list(zones.keys()))
        zone = random.choice(zones[city])
        request_type = random.choice(["ride", "food"])

        routing_key = f"{city}.{zone}.{request_type}"

        message = {
            "id": str(uuid.uuid4()),
            "city": city,
            "zone": zone,
            "type": request_type,
            "ts": datetime.now(timezone.utc).isoformat()
        }

        if message_count % 10 == 0:
            message.pop("zone")
            print(
                f"Sent BAD message (missing zone): "
                f"{routing_key} | {message['id']}"
            )
        else:
            print(f"Sent: {routing_key} | {message['id']}")

        channel.basic_publish(
            exchange="rapido-dispatch",
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2
            )
        )

        time.sleep(2)

except KeyboardInterrupt:
    print("\nDispatcher stopped.")

finally:
    connection.close()
