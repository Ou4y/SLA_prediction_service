import os
import pika
import json
from urllib.parse import urlparse
from training.retrain_sla import main as retrain_sla


def _rabbitmq_connection_parameters() -> pika.ConnectionParameters:
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


def callback(ch, method, properties, body):
    """
    Runs when a message is received.
    """
    message = json.loads(body)
    model_name = message.get("model")

    if model_name == "sla_model_v1":
        retrain_sla()

    # Tell RabbitMQ: job done
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consumer():
    connection = pika.BlockingConnection(_rabbitmq_connection_parameters())
    channel = connection.channel()

    channel.queue_declare(queue="model_retrain", durable=True)

    channel.basic_consume(
        queue="model_retrain",
        on_message_callback=callback,
    )

    print("Retraining worker is waiting for messages...")
    channel.start_consuming()


if __name__ == "__main__":
    start_consumer()