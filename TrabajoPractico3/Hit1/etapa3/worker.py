#!/usr/bin/env python3
"""
Worker Etapa 3: consume tareas desde cola durable y usa ack manual.
Si el worker se cae antes de ack, RabbitMQ reencola la tarea (reassign).
"""
import os
import sys
import json
import base64
import time

try:
    import cv2
except Exception:
    print("Error: falta 'cv2'. Instale opencv-python y numpy (ver requirements.txt)", file=sys.stderr)
    sys.exit(1)

import numpy as np
import pika

QUEUE_TASKS = "sobel_tasks"
QUEUE_RESULTS = "sobel_results"


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
    rabbit = os.environ.get("RABBIT_HOST", "rabbitmq-service")
    params = pika.ConnectionParameters(host=rabbit)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # Etapa 3: colas durables
    ch.queue_declare(queue=QUEUE_TASKS, durable=True)
    ch.queue_declare(queue=QUEUE_RESULTS, durable=True)
    # limitar a 1 tarea por worker activamente (fair dispatch)
    ch.basic_qos(prefetch_count=1)

    def on_task(ch, method, properties, body):
        try:
            msg = json.loads(body)
            cid = msg["id"]
            print(f"Worker {os.getpid()} procesando chunk {cid}...")
            img = decode_image_bytes(msg["data"])
            proc = apply_sobel_gray(img, ksize=3)
            out_msg = {
                "id": cid,
                "y0": msg["y0"],
                "y1": msg["y1"],
                "y0e": msg["y0e"],
                "y1e": msg["y1e"],
                "data": encode_image_bytes(proc)
            }
            # publicar resultado persistente
            ch.basic_publish(exchange="", routing_key=QUEUE_RESULTS, body=json.dumps(out_msg),
                             properties=pika.BasicProperties(delivery_mode=2))
            # ack de la tarea solo después de publicar el resultado
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"Worker {os.getpid()} terminado chunk {cid}")
        except Exception as e:
            print("Error en worker:", e, file=sys.stderr)
            # en caso de excepción, no ack -> message será reentregado cuando la conexión cierre o el worker muera

    # consumir con manual ack
    ch.basic_consume(queue=QUEUE_TASKS, on_message_callback=on_task, auto_ack=False)
    print("Worker listo (Etapa 3), esperando tareas...")
    ch.start_consuming()


if __name__ == "__main__":
    main()
