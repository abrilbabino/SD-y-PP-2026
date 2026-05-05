import json
import logging
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from logging.handlers import RotatingFileHandler

import pika


HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8080"))
TOTAL_MESSAGES = int(os.getenv("TOTAL_MESSAGES", "10"))


def setup_logger(name="producer"):
    """Configura logging estructurado hacia STDOUT y archivo rotativo."""
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    log_file = os.getenv("LOG_FILE", "/var/log/ex3/producer.log")
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=int(os.getenv("LOG_MAX_BYTES", "1048576")),
            backupCount=int(os.getenv("LOG_BACKUP_COUNT", "3")),
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        logger.warning(
            "No se pudo escribir en %s, continuando solo con stdout.", log_file
        )

    return logger


logger = setup_logger()


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return

        body = json.dumps({"servicio": "status"}).encode("utf-8")
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


def get_config():
    return {
        "user": os.getenv("RABBITMQ_USER", "tp3"),
        "password": os.getenv("RABBITMQ_PASS", "tp3"),
        "host": os.getenv("RABBITMQ_HOST", "rabbitmq"),
        "port": os.getenv("RABBITMQ_PORT", "5672"),
        "main_exchange": os.getenv("MAIN_EXCHANGE", "main_exchange"),
        "main_queue": os.getenv("MAIN_QUEUE", "main_queue"),
        "main_routing_key": os.getenv("MAIN_ROUTING_KEY", "tasks"),
        "dlx_exchange": os.getenv("DLX_EXCHANGE", "dlx_exchange"),
        "dead_letter_queue": os.getenv("DEAD_LETTER_QUEUE", "dead_letter_queue"),
        "dlq_routing_key": os.getenv("DLQ_ROUTING_KEY", "dead"),
    }


def build_rabbitmq_url(config):
    return (
        f"amqp://{config['user']}:{config['password']}"
        f"@{config['host']}:{config['port']}/"
    )


def connect_with_retry():
    config = get_config()
    retry_seconds = int(os.getenv("RABBITMQ_RETRY_SECONDS", "5"))

    while True:
        try:
            logger.info(
                "Conectando a RabbitMQ en %s:%s", config["host"], config["port"]
            )
            return pika.BlockingConnection(pika.URLParameters(build_rabbitmq_url(config)))
        except pika.exceptions.AMQPConnectionError:
            logger.warning(
                "RabbitMQ no esta listo. Reintentando en %ss...", retry_seconds
            )
            time.sleep(retry_seconds)


def declare_topology(channel, config):
    channel.exchange_declare(
        exchange=config["main_exchange"],
        exchange_type="direct",
        durable=True,
    )
    channel.exchange_declare(
        exchange=config["dlx_exchange"],
        exchange_type="direct",
        durable=True,
    )
    channel.queue_declare(
        queue=config["main_queue"],
        durable=True,
        arguments={
            "x-dead-letter-exchange": config["dlx_exchange"],
            "x-dead-letter-routing-key": config["dlq_routing_key"],
        },
    )
    channel.queue_declare(queue=config["dead_letter_queue"], durable=True)
    channel.queue_bind(
        exchange=config["main_exchange"],
        queue=config["main_queue"],
        routing_key=config["main_routing_key"],
    )
    channel.queue_bind(
        exchange=config["dlx_exchange"],
        queue=config["dead_letter_queue"],
        routing_key=config["dlq_routing_key"],
    )


def build_messages():
    messages = []
    for number in range(1, TOTAL_MESSAGES + 1):
        messages.append(
            {
                "id": number,
                "task": f"Tarea {number} de {TOTAL_MESSAGES}",
                #"error": number in {3, 7, 10}, #linea que genera errores para probar DLX
            }
        )
    return messages


def publish_messages(channel, config):
    for message in build_messages():
        body = json.dumps(message)
        channel.basic_publish(
            exchange=config["main_exchange"],
            routing_key=config["main_routing_key"],
            body=body,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
            ),
        )
        logger.info("Mensaje publicado: %s", body)


def main():
    start_health_server()

    config = get_config()
    connection = connect_with_retry()
    channel = connection.channel()
    declare_topology(channel, config)
    publish_messages(channel, config)
    connection.close()

    logger.info("Productor finalizo el envio y queda activo para /health.")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
