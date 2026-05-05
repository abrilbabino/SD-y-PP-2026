#!/usr/bin/env python3
import os
import sys
import time
import json
import base64
import argparse
import logging
from logging.handlers import RotatingFileHandler
from threading import Event

try:
    import cv2
except Exception:
    print("Error: falta 'cv2'. Instale opencv-python y numpy (ver requirements.txt)", file=sys.stderr)
    sys.exit(1)

import numpy as np
import pika

QUEUE_TASKS = "sobel_tasks"
QUEUE_RESULTS = "sobel_results"
OVERLAP = 1

# --- LOGGING ---

def setup_logger(name="master_etapa2"):
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

    log_file = os.getenv("LOG_FILE", "/var/log/ex4/master_etapa2.log")
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
        local_log = "master_etapa2.log"
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

def encode_image_bytes(img: np.ndarray) -> str:
    _, buf = cv2.imencode(".png", img)
    return base64.b64encode(buf.tobytes()).decode("ascii")

def decode_image_bytes(b64: str) -> np.ndarray:
    data = base64.b64decode(b64.encode("ascii"))
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    return img

def split_image(img: np.ndarray, n_chunks: int):
    h, w = img.shape
    base = h // n_chunks
    chunks = []
    for i in range(n_chunks):
        y0 = i * base
        y1 = (i + 1) * base - 1 if i < n_chunks - 1 else h - 1
        y0e = max(0, y0 - OVERLAP)
        y1e = min(h - 1, y1 + OVERLAP)
        chunk = img[y0e:y1e + 1, :].copy()
        chunks.append({
            "id": i,
            "y0": y0,
            "y1": y1,
            "y0e": y0e,
            "y1e": y1e,
            "data": chunk
        })
    return chunks

def assemble_image(h, w, results_dict, n_chunks):
    out = np.zeros((h, w), dtype=np.uint8)
    for i in range(n_chunks):
        meta = results_dict[i]["meta"]
        proc = results_dict[i]["img"]
        y0 = meta["y0"]
        y1 = meta["y1"]
        y0e = meta["y0e"]
        crop_top = y0 - y0e
        crop_h = (y1 - y0) + 1
        out[y0:y1 + 1, :] = proc[crop_top:crop_top + crop_h, :]
    return out


def main():
    parser = argparse.ArgumentParser(description="Master for distributed Sobel")
    parser.add_argument("--workers", type=int, default=4, help="Número de chunks/workers")
    parser.add_argument("--input", default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "inputSobel.jpeg")))
    parser.add_argument("--output", default=os.path.join(os.path.dirname(__file__), "outputSobel.png"))
    parser.add_argument("--rabbit", default=os.environ.get("RABBIT_HOST", "localhost"), help="Host RabbitMQ")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        logger.error("Archivo de entrada no encontrado: %s", args.input)
        sys.exit(2)

    img = cv2.imread(args.input, cv2.IMREAD_GRAYSCALE)
    if img is None:
        logger.error("No se pudo leer la imagen de entrada: %s", args.input)
        sys.exit(3)
    h, w = img.shape

    n = max(1, args.workers)
    logger.info("Dividiendo imagen en %d chunks...", n)
    chunks = split_image(img, n)

    try:
        params = pika.ConnectionParameters(host=args.rabbit)
        conn = pika.BlockingConnection(params)
        ch = conn.channel()
        ch.queue_declare(queue=QUEUE_TASKS)
        ch.queue_declare(queue=QUEUE_RESULTS)

        logger.info("Publicando tareas en RabbitMQ...")
        for c in chunks:
            payload = {
                "id": c["id"], "y0": c["y0"], "y1": c["y1"], "y0e": c["y0e"], "y1e": c["y1e"],
                "data": encode_image_bytes(c["data"])
            }
            ch.basic_publish(exchange="", routing_key=QUEUE_TASKS, body=json.dumps(payload))
            logger.info("Chunk %d publicado.", c['id'])

        results = {}
        done_event = Event()

        def on_result(ch, method, properties, body):
            try:
                msg = json.loads(body)
                cid = msg["id"]
                img_proc = decode_image_bytes(msg["data"])
                results[cid] = {"meta": {"y0": msg["y0"], "y1": msg["y1"], "y0e": msg["y0e"], "y1e": msg["y1e"]}, "img": img_proc}
                logger.info("Resultado de chunk %d recibido.", cid)
                if len(results) >= n:
                    done_event.set()
            except Exception as e:
                logger.error("Error procesando resultado: %s", e)

        res_conn = pika.BlockingConnection(params)
        res_ch = res_conn.channel()
        res_ch.queue_declare(queue=QUEUE_RESULTS)
        res_ch.basic_consume(queue=QUEUE_RESULTS, on_message_callback=on_result, auto_ack=True)

        logger.info("Esperando resultados...")
        import threading
        t = threading.Thread(target=res_ch.start_consuming, daemon=True)
        t.start()

        start = time.time()
        success = done_event.wait(timeout=300)
        elapsed = time.time() - start

        if res_ch.is_open:
            res_ch.stop_consuming()
        res_conn.close()
        conn.close()

        if not success or len(results) < n:
            logger.error("Error: solo se recibieron %d de %d resultados", len(results), n)
            sys.exit(4)

        logger.info("Ensamblando imagen final...")
        final = assemble_image(h, w, results, n)
        if cv2.imwrite(args.output, final):
            logger.info("Procesado distribuido finalizado. salida: %s  tiempo: %.3fs", args.output, elapsed)
        else:
            logger.error("Error al escribir imagen de salida: %s", args.output)
            sys.exit(5)

    except Exception as e:
        logger.error("Error de conexión o RabbitMQ: %s", e)
        sys.exit(6)


if __name__ == "__main__":
    main()
