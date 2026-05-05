#!/usr/bin/env python3
import os
import sys
import time
import json
import base64
import logging
from logging.handlers import RotatingFileHandler

try:
    import cv2
except Exception:
    print("Error: falta 'cv2'. Instale opencv-python y numpy (ver requirements.txt)", file=sys.stderr)
    sys.exit(1)

import numpy as np
import pika

QUEUE_TASKS = "sobel_tasks"
QUEUE_RESULTS = "sobel_results"

# --- LOGGING ---

def setup_logger(name="worker_etapa3"):
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

    log_file = os.getenv("LOG_FILE", "/var/log/ex4/worker_etapa3.log")
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=int(os.getenv("LOG_MAX_BYTES", "1048576")),
            backupCount=int(os.getenv("LOG_BACKUP_COUNT", "3")),
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (PermissionError, FileNotFoundError):
        local_log = "worker_etapa3.log"
        try:
            file_handler = RotatingFileHandler(local_log, maxBytes=1048576, backupCount=3)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.warning("No se pudo escribir en %s, usando log local %s", log_file, local_log)
        except Exception:
            logger.warning("No se pudo escribir en archivos de log, continuando solo con stdout.")

    return logger

logger = setup_logger()

# --- IMAGE LOGIC ---

def decode_image_bytes(b64: str):
    data = base64.b64decode(b64.encode("ascii"))
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    return img

def encode_image_bytes(img):
    _, buf = cv2.imencode(".png", img)
    return base64.b64encode(buf.tobytes()).decode("ascii")

def apply_sobel_gray(img_gray, ksize=3):
    sobelx = cv2.Sobel(img_gray, cv2.CV_64F, 1, 0, ksize=ksize)
    sobely = cv2.Sobel(img_gray, cv2.CV_64F, 0, 1, ksize=ksize)
    magnitude = np.sqrt(sobelx ** 2 + sobely ** 2)
    maxv = magnitude.max()
    if maxv == 0:
        return np.zeros_like(img_gray, dtype=np.uint8)
    return np.uint8(255 * (magnitude / maxv))


def main():
    rabbit = os.environ.get("RABBIT_HOST", "localhost")
    try:
        params = pika.ConnectionParameters(host=rabbit)
        conn = pika.BlockingConnection(params)
        ch = conn.channel()
        ch.queue_declare(queue=QUEUE_TASKS)
        ch.queue_declare(queue=QUEUE_RESULTS)

        # --- ETAPA 3: prefetch_count=1 para distribución justa ---
        ch.basic_qos(prefetch_count=1)

        def on_task(ch, method, properties, body):
            try:
                msg = json.loads(body)
                cid = msg["id"]
                logger.info("Procesando chunk %d...", cid)
                img = decode_image_bytes(msg["data"])
                proc = apply_sobel_gray(img, ksize=3)
                out_msg = {
                    "id": cid, "y0": msg["y0"], "y1": msg["y1"], "y0e": msg["y0e"], "y1e": msg["y1e"],
                    "data": encode_image_bytes(proc)
                }
                ch.basic_publish(exchange="", routing_key=QUEUE_RESULTS, body=json.dumps(out_msg))
                # --- ETAPA 3: ACK manual DESPUÉS de publicar el resultado ---
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info("Chunk %d terminado y resultado publicado.", cid)
            except Exception as e:
                logger.error("Error en procesamiento: %s", e)
                # NACK sin requeue para evitar loops infinitos en mensajes corruptos
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        # --- ETAPA 3: auto_ack=False para ACK manual ---
        ch.basic_consume(queue=QUEUE_TASKS, on_message_callback=on_task, auto_ack=False)
        logger.info("Worker listo, esperando tareas en RabbitMQ (%s)...", rabbit)
        ch.start_consuming()
    except Exception as e:
        logger.error("Error de conexión o RabbitMQ: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
