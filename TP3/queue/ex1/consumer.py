import os
import time
from datetime import datetime

import pika


QUEUE_NAME = "task_queue"


def connect_with_retry():
    """Se conecta a RabbitMQ reintentando hasta que el broker este listo."""
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://tp3:tp3@rabbitmq:5672/")
    retry_seconds = int(os.getenv("RABBITMQ_RETRY_SECONDS", "5"))

    while True:
        try:
            print(f"Conectando a RabbitMQ: {rabbitmq_url}")
            parameters = pika.URLParameters(rabbitmq_url)
            return pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError:
            print(f"RabbitMQ no esta listo. Reintentando en {retry_seconds}s...")
            time.sleep(retry_seconds)


def main():
    consumer_id = os.getenv("CONSUMER_ID", "consumer-local")
    processing_seconds = float(os.getenv("PROCESSING_SECONDS", "1"))

    connection = connect_with_retry()
    channel = connection.channel()

    # El consumidor declara la misma cola que el productor.
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    # Recibir solo un mensaje sin confirmar ayuda a ver el reparto entre consumidores.
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        message = body.decode("utf-8")
        received_at = datetime.now().isoformat(timespec="seconds")
        print(f"{received_at} [{consumer_id}] Recibio: {message}", flush=True)

        # Simula procesamiento para que el round-robin sea facil de observar.
        time.sleep(processing_seconds)

        # ACK manual: se confirma el mensaje despues de procesarlo.
        ch.basic_ack(delivery_tag=method.delivery_tag)
        confirmed_at = datetime.now().isoformat(timespec="seconds")
        print(f"{confirmed_at} [{consumer_id}] Confirmo: {message}", flush=True)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print(f"[{consumer_id}] Esperando mensajes...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
