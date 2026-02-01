import os
import pika
import json
from urllib.parse import urlparse


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
        return pika.ConnectionParameters(host=host, port=port, virtual_host=vhost, credentials=credentials)

    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")

    credentials = pika.PlainCredentials(user, password)
    return pika.ConnectionParameters(host=host, port=port, credentials=credentials)


def publish_retrain_event(model_name: str):
    connection = pika.BlockingConnection(_rabbitmq_connection_parameters())
    channel = connection.channel()

    channel.queue_declare(queue="model_retrain", durable=True)

    message = {"model": model_name}

    channel.basic_publish(
        exchange="",
        routing_key="model_retrain",
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    
