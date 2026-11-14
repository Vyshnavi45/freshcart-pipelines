
import json
import os
import sys
import time
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import pika
from dotenv import load_dotenv

# Locate the project folders
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "elt"))

import extract
import snowflake_io as sf

from run_pipeline import quality_checks

load_dotenv(ROOT / ".env")

AMQP_URL = os.environ.get("AMQP_URL")

if not AMQP_URL:
    raise RuntimeError("Please set AMQP_URL first.")

SQL = ROOT / "elt" / "sql"

run_date = date(2026, 9, 3)
run_id = "stream_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

orders = []
delivery_tags = []

# Connect to RabbitMQ
connection = pika.BlockingConnection(
    pika.URLParameters(AMQP_URL)
)
channel = connection.channel()

channel.exchange_declare(
    exchange="rapido-dispatch",
    exchange_type="topic",
    durable=True
)

channel.queue_declare(
    queue="freshcart-orders",
    durable=True
)

channel.queue_bind(
    exchange="rapido-dispatch",
    queue="freshcart-orders",
    routing_key="freshcart.orders"
)


def receive_order(ch, method, properties, body):
    try:
        order = json.loads(body)

        required = [
            "order_id", "cust_email", "cust_name",
            "order_date", "amount", "currency",
            "pincode", "updated_at"
        ]

        if not isinstance(order, dict) or not all(
            field in order for field in required
        ):
            print("Rejected invalid order")
            ch.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False
            )
            return

        orders.append(order)
        delivery_tags.append(method.delivery_tag)

        print("Received:", order["order_id"])

    except Exception as error:
        print("Invalid message:", error)
        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False
        )


channel.basic_qos(prefetch_count=100)
channel.basic_consume(
    queue="freshcart-orders",
    on_message_callback=receive_order,
    auto_ack=False
)

print("Waiting for FreshCart orders for 60 seconds...")

deadline = time.monotonic() + 60

try:
    while time.monotonic() < deadline:
        connection.process_data_events(time_limit=1)

finally:
    channel.stop_consuming()

# Save collected messages as a raw landing file
landing_file = extract.write_landing(
    "web", orders, run_id, run_date
)

# Acknowledge messages only after the raw file is saved
for tag in delivery_tags:
    channel.basic_ack(delivery_tag=tag)

connection.close()

if not orders:
    print("No orders received. Nothing to load.")
    sys.exit(0)

print("Saved raw file:", landing_file)

# Connect to Snowflake
conn = sf.connect()

try:
    variables = {
        "run_id": run_id,
        "run_date": run_date.isoformat()
    }

    # Load streamed orders into Bronze
    loaded = sf.load_file(
        conn,
        landing_file,
        "bronze.orders_raw",
        f"orders_web/{run_date.isoformat()}/{run_id}"
    )

    print("Rows loaded into Bronze:", loaded)

    # Run the existing transformations
    sf.run_sql_file(
        conn, SQL / "10_silver_orders_clean.sql", variables
    )

    sf.run_sql_file(
        conn, SQL / "20_silver_orders_dedup.sql", variables
    )

    # Look up any pincodes not already present
    pins = [
        row[0] for row in sf.query_all(
            conn,
            """
            SELECT DISTINCT o.pincode
            FROM silver.orders_dedup o
            WHERE NOT EXISTS (
                SELECT 1
                FROM ref.pincode_geo g
                WHERE g.pincode = o.pincode
            )
            """
        )
    ]

    pin_file = extract.write_landing(
        "pincode",
        extract.pincodes(extract.http_session(), pins, mock=True),
        run_id,
        run_date
    )

    sf.load_file(
        conn,
        pin_file,
        "bronze.pincode_raw",
        f"pincode/{run_date.isoformat()}/{run_id}"
    )

    sf.run_sql_file(
        conn, SQL / "30_dim_customers_scd2.sql", variables
    )

    sf.run_sql_file(
        conn, SQL / "31_ref_fx_daily.sql", variables
    )

    sf.run_sql_file(
        conn, SQL / "32_ref_pincode_geo.sql", variables
    )

    sf.run_sql_file(
        conn, SQL / "40_gold_fct_orders.sql", variables
    )

    # Validate and display Gold totals
    quality_checks(conn, False)

    totals = sf.query_one(
        conn,
        """
        SELECT COUNT(*), SUM(amount_inr), SUM(loyalty_points)
        FROM gold.fct_orders
        """
    )

    print("\nFreshCart streaming completed!")
    print("Gold orders:", totals[0])
    print("Gold revenue:", totals[1])
    print("Loyalty points:", totals[2])

finally:
    conn.close()
