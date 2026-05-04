#!/usr/bin/env python3
"""
Master (splitter + joiner). Divide inputSobel.jpeg en N chunks, publica tareas a RabbitMQ
y espera los resultados para crear etapa2/outputSobel.png.

Ejemplo:
  export RABBIT_HOST=rabbitmq
  python3 master.py --workers 4
"""
import os
import sys
import time
import json
import base64
import argparse
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
OVERLAP = 1  # halo para evitar artefactos en bordes


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
        # crop within processed chunk to remove overlap
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
        print(f"Error: archivo de entrada no encontrado: {args.input}", file=sys.stderr)
        sys.exit(2)

    img = cv2.imread(args.input, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("Error: no se pudo leer la imagen de entrada", file=sys.stderr)
        sys.exit(3)
    h, w = img.shape

    # split
    n = max(1, args.workers)
    chunks = split_image(img, n)

    # preparar conexión RabbitMQ
    params = pika.ConnectionParameters(host=args.rabbit)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    # ETAPA 2: sin durabilidad ni tolerancia a fallos
    # (colocar durable=True y persistencia se hará en etapa3 si corresponde)
    ch.queue_declare(queue=QUEUE_TASKS)
    ch.queue_declare(queue=QUEUE_RESULTS)

    # publicar tareas
    for c in chunks:
        payload = {
            "id": c["id"],
            "y0": c["y0"],
            "y1": c["y1"],
            "y0e": c["y0e"],
            "y1e": c["y1e"],
            "data": encode_image_bytes(c["data"])
        }
        ch.basic_publish(
            exchange="",
            routing_key=QUEUE_TASKS,
            body=json.dumps(payload)
        )
        print(f"Publicado chunk {c['id']} (rows {c['y0e']}..{c['y1e']})")

    # preparar consumidor para resultados
    results = {}
    done_event = Event()

    def on_result(ch, method, properties, body):
        try:
            msg = json.loads(body)
            cid = msg["id"]
            img_proc = decode_image_bytes(msg["data"])
            results[cid] = {"meta": {"y0": msg["y0"], "y1": msg["y1"], "y0e": msg["y0e"], "y1e": msg["y1e"]}, "img": img_proc}
            print(f"Recibido resultado chunk {cid}")
            if len(results) >= n:
                done_event.set()
        except Exception as e:
            print("Error procesando resultado:", e, file=sys.stderr)
        # NOTE: en Etapa 2 no hacemos ack manual ni reencolado; usamos auto_ack al consumir.

    res_conn = pika.BlockingConnection(params)
    res_ch = res_conn.channel()
    # ETAPA 2: consumo sin tolerancia a fallos (auto_ack)
    res_ch.queue_declare(queue=QUEUE_RESULTS)
    res_ch.basic_consume(queue=QUEUE_RESULTS, on_message_callback=on_result, auto_ack=True)

    # esperar resultados en hilo de consumo (start_consuming es bloqueante)
    print("Esperando resultados...")
    # correr start_consuming en thread-like (BlockingConnection no tiene timeout stop, usar loop y check)
    import threading
    t = threading.Thread(target=res_ch.start_consuming, daemon=True)
    t.start()

    start = time.time()
    # esperar hasta recibir todos
    done_event.wait(timeout=300)  # timeout de 5 min
    elapsed = time.time() - start

    # detener consumidor
    try:
        if res_ch.is_open:
            res_ch.stop_consuming()
    except Exception:
        pass
    res_conn.close()
    conn.close()

    if len(results) < n:
        print(f"Error: solo se recibieron {len(results)} de {n} resultados", file=sys.stderr)
        sys.exit(4)

    final = assemble_image(h, w, results, n)
    ok = cv2.imwrite(args.output, final)
    if not ok:
        print("Error: no se pudo escribir la imagen de salida", file=sys.stderr)
        sys.exit(5)

    print(f"Procesado distribuido finalizado. salida: {args.output}  tiempo: {elapsed:.3f}s")


if __name__ == "__main__":
    main()
