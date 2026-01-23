import pika
import json

def publish_retrain_event(model_name: str):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq")
    )
    channel = connection.channel()

    channel.queue_declare(queue="model_retrain")

    message = {
        "model": model_name
    }

    channel.basic_publish(
        exchange="",
        routing_key="model_retrain",
        body=json.dumps(message)
    )

    connection.close()