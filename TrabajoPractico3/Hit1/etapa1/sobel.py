#!/usr/bin/env python3
"""
Aplicación centralizada: toma TrabajoPractico3/Hit1/inputSobel.jpeg,
aplica el filtro Sobel y escribe TrabajoPractico3/Hit1/etapa1/outputSobel.png.

Ejecutar desde la raíz del proyecto:

    (si falta alguna dependencia hacer):
        sudo apt update
        sudo apt install -y python3-opencv python3-numpy


  python3 TrabajoPractico3/Hit1/etapa1/sobel.py
"""
import os
import sys
import time

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
        print(f"Error: no se encontró la imagen de entrada esperada:\n  {input_path}\n"
              "Coloque inputSobel.jpeg dentro de la carpeta Hit1 (una carpeta arriba de etapa1).",
              file=sys.stderr)
        sys.exit(2)

    start = time.time()
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error: no se pudo leer la imagen (formato inválido o archivo corrupto):\n  {input_path}",
              file=sys.stderr)
        sys.exit(3)

    result = apply_sobel_gray(img, ksize=3)
    ok = cv2.imwrite(output_path, result)
    elapsed = time.time() - start

    if not ok:
        print(f"Error: no se pudo escribir el archivo de salida:\n  {output_path}", file=sys.stderr)
        sys.exit(4)

    print(f"Procesado exitoso:\n  entrada: {input_path}\n  salida:   {output_path}\n  tiempo: {elapsed:.3f}s")


if __name__ == "__main__":
    main()
