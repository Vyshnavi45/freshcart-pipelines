
import json
import os
import sys

import pika

if len(sys.argv) != 3:
    print("Usage: py stream/driver.py NAME PATTERN")
    sys.exit(1)

driver_name = sys.argv[1]
binding_pattern = sys.argv[2]

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

result = channel.queue_declare(queue="", exclusive=True)
queue_name = result.method.queue

channel.queue_bind(
    exchange="rapido-dispatch",
    queue=queue_name,
    routing_key=binding_pattern
)

print(f"{driver_name} listening for: {binding_pattern}")


def callback(ch, method, properties, body):
    try:
        message = json.loads(body)

        if "zone" not in message:
            print(
                f"{driver_name} rejected message "
                f"(missing zone): {method.routing_key}"
            )
            ch.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False
            )
            return

        print(
            f"{driver_name} received {method.routing_key}: "
            f"{message}"
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as error:
        print(f"Error processing message: {error}")
        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False
        )


channel.basic_qos(prefetch_count=1)
channel.basic_consume(
    queue=queue_name,
    on_message_callback=callback,
    auto_ack=False
)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print(f"\n{driver_name} stopped.")
finally:
    if connection.is_open:
        connection.close()
