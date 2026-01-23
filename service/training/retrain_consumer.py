import pika
import json
from training.retrain_sla import main as retrain_sla

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
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq")
    )
    channel = connection.channel()

    channel.queue_declare(queue="model_retrain")

    channel.basic_consume(
        queue="model_retrain",
        on_message_callback=callback
    )

    print("Retraining worker is waiting for messages...")
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()