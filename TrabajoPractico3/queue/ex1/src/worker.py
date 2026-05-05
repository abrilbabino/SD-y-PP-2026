import json
import logging
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from logging.handlers import RotatingFileHandler

import pika


HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8081"))


def setup_logger(name="worker"):
    """Configura logs para STDOUT y archivo rotativo en disco."""
    log_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    # Salida estándar (para Kubernetes/Docker logs)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)

    # Salida a archivo rotativo
    log_file = os.getenv("LOG_FILE", "/var/log/ex1/worker.log")
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=int(os.getenv("LOG_MAX_BYTES", "1048576")),
            backupCount=int(os.getenv("LOG_BACKUP_COUNT", "3")),
        )
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        logger.warning(
            "No se pudo escribir en %s, continuando solo con stdout.", log_file
        )

    return logger


logger = setup_logger()


class HealthHandler(BaseHTTPRequestHandler):
    """Endpoint HTTP usado por Kubernetes para verificar salud."""

    def do_GET(self):
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return

        response = {"servicio": "status"}
        body = json.dumps(response).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def start_health_server():
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Health-check disponible en /health puerto %s", HEALTH_PORT)


def build_rabbitmq_url():
    user = os.getenv("RABBITMQ_USER", "tp3")
    password = os.getenv("RABBITMQ_PASS", "tp3")
    host = os.getenv("RABBIT_HOST", "rabbitmq")
    port = os.getenv("RABBITMQ_PORT", "5672")
    return f"amqp://{user}:{password}@{host}:{port}/"


def get_queue_name():
    return os.getenv("QUEUE_NAME", "task_queue")


def connect_with_retry():
    """Se conecta a RabbitMQ reintentando hasta que el broker este listo."""
    rabbitmq_url = build_rabbitmq_url()
    retry_seconds = int(os.getenv("RABBITMQ_RETRY_SECONDS", "5"))

    while True:
        try:
            logger.info(
                "Conectando a RabbitMQ en %s:%s",
                os.getenv("RABBIT_HOST", "rabbitmq"),
                os.getenv("RABBITMQ_PORT", "5672"),
            )
            parameters = pika.URLParameters(rabbitmq_url)
            return pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError:
            logger.warning(
                "RabbitMQ no esta listo. Reintentando en %ss...", retry_seconds
            )
            time.sleep(retry_seconds)


def main():
    worker_id = os.getenv("WORKER_ID", "worker-local")
    processing_seconds = float(os.getenv("PROCESSING_SECONDS", "1"))

    start_health_server()

    connection = connect_with_retry()
    channel = connection.channel()
    queue_name = get_queue_name()

    # La cola durable sobrevive reinicios del broker si RabbitMQ tuviera persistencia.
    channel.queue_declare(queue=queue_name, durable=True)

    # Un mensaje sin confirmar por worker permite observar mejor el reparto.
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        message = body.decode("utf-8")
        logger.info("[%s] Recibio: %s", worker_id, message)

        # Simula procesamiento de una tarea.
        time.sleep(processing_seconds)

        # ACK manual: se confirma solo despues de procesar.
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("[%s] Confirmo: %s", worker_id, message)

    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    logger.info("[%s] Esperando tareas en %s...", worker_id, queue_name)
    channel.start_consuming()


if __name__ == "__main__":
    main()
