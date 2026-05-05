#!/usr/bin/env python3
"""
Master (splitter + joiner) para Etapa 3 (Kubernetes + tolerancia por reassign vía RabbitMQ acks).
Publica tareas persistentes en cola durable; espera resultados y arma output.
Uso: python3 master.py --workers N --input /path/to/inputSobel.jpeg --output /path/to/output.png
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
    print("Error: falta 'cv2'. Instale dependencias (opencv-python, numpy, pika).", file=sys.stderr)
    sys.exit(1)

import numpy as np
import pika

QUEUE_TASKS = "sobel_tasks"
QUEUE_RESULTS = "sobel_results"
OVERLAP = 1


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--input", required=False, default=os.environ.get("INPUT_PATH"))
    parser.add_argument("--output", required=False, default=None)
    parser.add_argument("--rabbit", default=os.environ.get("RABBIT_HOST", "rabbitmq-service"))
    args = parser.parse_args()

    # Resolver ruta de entrada: usar INPUT_PATH env / arg si existe, o buscar en rutas candidatas
    if args.input:
        input_candidates = [args.input]
    else:
        input_candidates = [
            "/app/etapa3/data/inputSobel.jpeg",   # hostPath mount suggested in manifests
            "/app/etapa3/inputSobel.jpeg",        # if image includes the file
            "/inputSobel.jpeg",
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "inputSobel.jpeg"))
        ]

    input_path = None
    for p in input_candidates:
        if p and os.path.exists(p):
            input_path = p
            break

    if not input_path:
        print("Error: archivo de entrada no encontrado. Buscado en:\n  " + "\n  ".join(input_candidates), file=sys.stderr)
        sys.exit(2)

    # output por defecto: misma carpeta que la entrada
    if args.output:
        output_path = args.output
    else:
        out_dir = os.path.dirname(input_path)
        output_path = os.path.join(out_dir, "outputSobel.png")

    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("Error: no se pudo leer la imagen de entrada:", input_path, file=sys.stderr)
        sys.exit(3)
    h, w = img.shape

    n = max(1, args.workers)
    chunks = split_image(img, n)

    # conectar RabbitMQ
    params = pika.ConnectionParameters(host=args.rabbit)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # ETAPA 3: usar colas durables y mensajes persistentes para permitir reassign si worker falla
    ch.queue_declare(queue=QUEUE_TASKS, durable=True)
    ch.queue_declare(queue=QUEUE_RESULTS, durable=True)

    # publicar tareas persistentes
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
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2)  # mark message persistent
        )
        print(f"Publicado chunk {c['id']} (rows {c['y0e']}..{c['y1e']})")

    # consumir resultados (en Etapa 3 podemos aceptar auto_ack para resultados)
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

    res_conn = pika.BlockingConnection(params)
    res_ch = res_conn.channel()
    res_ch.queue_declare(queue=QUEUE_RESULTS, durable=True)
    res_ch.basic_consume(queue=QUEUE_RESULTS, on_message_callback=on_result, auto_ack=True)

    import threading
    t = threading.Thread(target=res_ch.start_consuming, daemon=True)
    t.start()

    start = time.time()
    done_event.wait(timeout=600)
    elapsed = time.time() - start

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
    ok = cv2.imwrite(output_path, final)
    if not ok:
        print("Error: no se pudo escribir la imagen de salida:", output_path, file=sys.stderr)
        sys.exit(5)

    print(f"Procesado distribuido finalizado. salida: {output_path}  tiempo: {elapsed:.3f}s")


if __name__ == "__main__":
    main()