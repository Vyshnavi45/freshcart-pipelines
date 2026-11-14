
import json
import os
import time
import pika
from datetime import datetime, timezone

AMQP_URL = os.environ.get("AMQP_URL")

if not AMQP_URL:
    raise RuntimeError("Please set AMQP_URL first.")

connection = pika.BlockingConnection(
    pika.URLParameters(AMQP_URL)
)
channel = connection.channel()

channel.exchange_declare(
    exchange="rapido-dispatch",
    exchange_type="topic",
    durable=True
)

orders = [
    {
        "order_id": "ORD-STREAM-9001",
        "cust_email": "priya.r@gmail.com",
        "cust_name": "Priya R",
        "order_date": "2026-09-03",
        "amount": "1500.00",
        "currency": "INR",
        "pincode": "600041",
        "updated_at": "2026-09-03 17:00:00"
    },
    {
        "order_id": "ORD-STREAM-9002",
        "cust_email": "arjun.k@yahoo.in",
        "cust_name": "Arjun K",
        "order_date": "2026-09-03",
        "amount": "2200.00",
        "currency": "INR",
        "pincode": "560034",
        "updated_at": "2026-09-03 17:05:00"
    },
    {
        "order_id": "ORD-STREAM-9003",
        "cust_email": "meera@outlook.com",
        "cust_name": "Meera S",
        "order_date": "2026-09-03",
        "amount": "1800.00",
        "currency": "INR",
        "pincode": "400050",
        "updated_at": "2026-09-03 17:10:00"
    }
]

try:
    for order in orders:
        channel.basic_publish(
            exchange="rapido-dispatch",
            routing_key="freshcart.orders",
            body=json.dumps(order),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2
            )
        )

        print("Sent:", order["order_id"])
        time.sleep(2)

    print("All 3 FreshCart orders sent successfully.")

finally:
    connection.close()
