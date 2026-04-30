import os
import time

import pika


QUEUE_NAME = "task_queue"
TOTAL_MESSAGES = 10


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
    connection = connect_with_retry()
    channel = connection.channel()

    # Declarar la cola es seguro aunque ya exista.
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    for number in range(1, TOTAL_MESSAGES + 1):
        message = f"Tarea {number} de {TOTAL_MESSAGES}"

        # routing_key es el nombre de la cola cuando se usa el exchange por defecto.
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        print(f"Mensaje enviado: {message}")

    connection.close()
    print("Productor finalizado.")


if __name__ == "__main__":
    main()
