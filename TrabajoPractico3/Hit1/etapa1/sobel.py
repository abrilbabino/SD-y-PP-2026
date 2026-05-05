#!/usr/bin/env python3
"""
Aplicación centralizada: toma TrabajoPractico3/Hit1/inputSobel.jpeg,
aplica el filtro Sobel y escribe TrabajoPractico3/Hit1/etapa1/outputSobel.png.
"""
import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler

# intentar importar OpenCV y dar instrucción clara si falta
try:
    import cv2
except Exception:
    print(
        "Error: falta el módulo 'cv2' (opencv-python).\n"
        "Instale las dependencias con:\n"
        "  python3 -m pip install --user -r TrabajoPractico3/Hit1/etapa1/requirements.txt\n",
        file=sys.stderr,
    )
    sys.exit(1)

import numpy as np

# --- LOGGING ---

def setup_logger(name="sobel_central"):
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

    log_file = os.getenv("LOG_FILE", "/var/log/ex4/sobel_central.log")
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
        local_log = "sobel_central.log"
        try:
            file_handler = RotatingFileHandler(local_log, maxBytes=1048576, backupCount=3)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.warning("No se pudo escribir en %s, usando log local %s", log_file, local_log)
        except Exception:
            logger.warning("No se pudo escribir en archivos de log, continuando solo con stdout.")

    return logger

logger = setup_logger()

# --- PROCESSING ---

def apply_sobel_gray(img_gray: np.ndarray, ksize: int = 3) -> np.ndarray:
    # Calcular derivadas en X y Y (float64 para conservar rango)
    sobelx = cv2.Sobel(img_gray, cv2.CV_64F, 1, 0, ksize=ksize)
    sobely = cv2.Sobel(img_gray, cv2.CV_64F, 0, 1, ksize=ksize)
    # Magnitud del gradiente
    magnitude = np.sqrt(sobelx ** 2 + sobely ** 2)
    maxv = magnitude.max()
    if maxv == 0:
        return np.zeros_like(img_gray, dtype=np.uint8)
    # Normalizar a 0-255
    norm = np.uint8(255 * (magnitude / maxv))
    return norm


def main():
    # input: ../inputSobel.jpeg (carpeta Hit1), output: ./outputSobel.png (carpeta etapa1)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.abspath(os.path.join(script_dir, "..", "inputSobel.jpeg"))
    output_path = os.path.join(script_dir, "outputSobel.png")

    if not os.path.exists(input_path):
        logger.error("Archivo de entrada no encontrado: %s", input_path)
        sys.exit(2)

    start = time.time()
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        logger.error("No se pudo leer la imagen (formato inválido o archivo corrupto): %s", input_path)
        sys.exit(3)

    logger.info("Aplicando filtro Sobel a la imagen...")
    result = apply_sobel_gray(img, ksize=3)
    ok = cv2.imwrite(output_path, result)
    elapsed = time.time() - start

    if not ok:
        logger.error("No se pudo escribir el archivo de salida: %s", output_path)
        sys.exit(4)

    logger.info("Procesado exitoso: tiempo %.3fs", elapsed)
    logger.info("  entrada: %s", input_path)
    logger.info("  salida:  %s", output_path)


if __name__ == "__main__":
    main()
