import json
import logging
import os
import random
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from logging.handlers import RotatingFileHandler

import pika


HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8081"))
BACKOFF_SECONDS = [1, 2, 4, 8]
MAX_RETRIES = len(BACKOFF_SECONDS)


def setup_logger(name="main-consumer"):
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

    log_file = os.getenv("LOG_FILE", "/var/log/ex4/consumer.log")
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
        "retry_exchange": os.getenv("RETRY_EXCHANGE", "retry_exchange"),
        "retry_queue": os.getenv("RETRY_QUEUE", "retry_queue"),
        "retry_routing_key": os.getenv("RETRY_ROUTING_KEY", "retry"),
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
    channel.exchange_declare(
        exchange=config["retry_exchange"],
        exchange_type="direct",
        durable=True,
    )
    channel.queue_declare(
        queue=config["main_queue"],
        durable=True,
    )
    channel.queue_declare(
        queue=config["retry_queue"],
        durable=True,
        arguments={
            "x-dead-letter-exchange": config["main_exchange"],
            "x-dead-letter-routing-key": config["main_routing_key"],
        },
    )
    channel.queue_declare(queue=config["dead_letter_queue"], durable=True)
    channel.queue_bind(
        exchange=config["main_exchange"],
        queue=config["main_queue"],
        routing_key=config["main_routing_key"],
    )
    channel.queue_bind(
        exchange=config["retry_exchange"],
        queue=config["retry_queue"],
        routing_key=config["retry_routing_key"],
    )
    channel.queue_bind(
        exchange=config["dlx_exchange"],
        queue=config["dead_letter_queue"],
        routing_key=config["dlq_routing_key"],
    )


def should_fail():
    failure_probability = float(os.getenv("FAILURE_PROBABILITY", "0.5"))
    return random.random() < failure_probability


def get_retry_attempt(properties):
    headers = getattr(properties, "headers", None) or {}
    return int(headers.get("x-retry-attempt", 0))


def get_backoff_seconds(attempt):
    return BACKOFF_SECONDS[attempt - 1]


def publish_retry(channel, config, body, attempt, wait_seconds):
    headers = {"x-retry-attempt": attempt}
    channel.basic_publish(
        exchange=config["retry_exchange"],
        routing_key=config["retry_routing_key"],
        body=body,
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            expiration=str(wait_seconds * 1000),
            headers=headers,
        ),
    )


def publish_to_dlq(channel, config, body, attempt):
    headers = {"x-retry-attempt": attempt, "x-final-failure": True}
    channel.basic_publish(
        exchange=config["dlx_exchange"],
        routing_key=config["dlq_routing_key"],
        body=body,
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            headers=headers,
        ),
    )


def main():
    start_health_server()

    config = get_config()
    connection = connect_with_retry()
    channel = connection.channel()
    declare_topology(channel, config)
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        try:
            message = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            logger.exception("Mensaje invalido. Se envia a DLQ: %s", body)
            publish_to_dlq(ch, config, body, 0)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        attempt = get_retry_attempt(properties)
        if should_fail():
            next_attempt = attempt + 1
            if next_attempt > MAX_RETRIES:
                logger.error(
                    "Mensaje enviado a DLQ luego de %s reintentos fallidos: %s",
                    MAX_RETRIES,
                    message,
                )
                publish_to_dlq(ch, config, body, MAX_RETRIES)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            wait_seconds = get_backoff_seconds(next_attempt)
            logger.warning(
                "Fallo al procesar mensaje id=%s. Intento %s/%s. "
                "Reencolando con espera de %ss.",
                message.get("id"),
                next_attempt,
                MAX_RETRIES,
                wait_seconds,
            )
            publish_retry(ch, config, body, next_attempt, wait_seconds)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        logger.info(
            "Mensaje procesado correctamente en intento %s: %s",
            attempt + 1,
            message,
        )
        time.sleep(float(os.getenv("PROCESSING_SECONDS", "1")))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=config["main_queue"], on_message_callback=callback)
    logger.info("Esperando mensajes en %s...", config["main_queue"])
    channel.start_consuming()


if __name__ == "__main__":
    main()
