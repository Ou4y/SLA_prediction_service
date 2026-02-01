import json
import os
from urllib.parse import urlparse

import pika

# Import the internal prediction logic
from app.main import prepare_features
from app.sla_model import predict_sla_risk


def _rabbitmq_connection_parameters() -> pika.ConnectionParameters:
    """Build `pika.ConnectionParameters` from env.

    Priority:
    1) RABBITMQ_URL (amqp://user:pass@host:port/vhost)
    2) RABBITMQ_HOST / RABBITMQ_PORT / RABBITMQ_USER / RABBITMQ_PASSWORD
    """
    url = os.getenv("RABBITMQ_URL")
    if url:
        parsed = urlparse(url)
        host = parsed.hostname or "rabbitmq"
        port = parsed.port or 5672
        user = parsed.username or os.getenv("RABBITMQ_USER", "guest")
        password = parsed.password or os.getenv("RABBITMQ_PASSWORD", "guest")
        vhost = (parsed.path or "/").lstrip("/") or "/"

        credentials = pika.PlainCredentials(user, password)
        return pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=vhost,
            credentials=credentials,
        )

    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")

    credentials = pika.PlainCredentials(user, password)
    return pika.ConnectionParameters(host=host, port=port, credentials=credentials)


def _coerce_ticket_message_to_request_dict(message: dict) -> dict:
    """Map ticket-service payload into the fields the SLA model expects.

    Expected output keys:
      support_level, priority, created_hour, created_day, assigned_team

    This is intentionally defensive because the ticket payload shape may evolve.
    """
    # Common nesting patterns: {ticket: {...}} or flat JSON
    src = message.get("ticket") if isinstance(message.get("ticket"), dict) else message

    def pick(*keys, default=None):
        for k in keys:
            if k in src and src[k] is not None:
                return src[k]
        return default

    return {
        "support_level": pick("support_level", "supportLevel"),
        "priority": pick("priority"),
        "created_hour": int(pick("created_hour", "createdHour", default=0)),
        "created_day": pick("created_day", "createdDay"),
        "assigned_team": pick("assigned_team", "assignedTeam"),
    }


def _predict_sla_probability(ticket_request: dict) -> float:
    """Run the SLA model and return breach probability."""
    # We reuse prepare_features by creating a lightweight object
    class _Req:
        def __init__(self, d: dict):
            self.support_level = d["support_level"]
            self.priority = d["priority"]
            self.created_hour = d["created_hour"]
            self.created_day = d["created_day"]
            self.assigned_team = d["assigned_team"]

    req = _Req(ticket_request)
    features = prepare_features(req)
    return float(predict_sla_risk(features)[0])


def callback(ch, method, properties, body):
    """Called when a ticket-created message is received."""
    try:
        message = json.loads(body)
        ticket_request = _coerce_ticket_message_to_request_dict(message)

        # Validate required fields
        missing = [k for k, v in ticket_request.items() if v is None]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        prob = _predict_sla_probability(ticket_request)

        # For now we just log. Next step is to publish to a response queue or store in DB.
        ticket_id = message.get("ticket_id") or message.get("id") or (message.get("ticket") or {}).get("id")
        print(
            json.dumps(
                {
                    "event": "ticket_created",
                    "ticket_id": ticket_id,
                    "sla_breach_probability": round(prob, 6),
                }
            )
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        # Don't lose the message silently; reject and requeue unless you prefer dead-lettering.
        print(f"ticket_consumer error: {exc}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consumer():
    connection = pika.BlockingConnection(_rabbitmq_connection_parameters())
    channel = connection.channel()

    # Queue name must match what ticket-service publishes to.
    queue_name = os.getenv("TICKET_CREATED_QUEUE", "ticket_created")

    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(queue=queue_name, on_message_callback=callback)

    print(f"Ticket consumer is waiting for messages on queue '{queue_name}'...")
    channel.start_consuming()


if __name__ == "__main__":
    start_consumer()
