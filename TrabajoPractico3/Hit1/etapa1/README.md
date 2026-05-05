# Etapa 1 — Sobel (centralizado)

Descripción
- Script: `sobel.py`
- Comportamiento: toma la imagen de entrada `TrabajoPractico3/Hit1/inputSobel.jpeg`, aplica el operador de Sobel y escribe la salida en `TrabajoPractico3/Hit1/etapa1/outputSobel.png`.

Prerequisitos
- Python 3
- OpenCV y NumPy (ver opciones de instalación abajo)

Instalación (recomendado: pip)
Desde la raíz del proyecto:
  python3 -m pip install --user -r requirements.txt

O (Debian/Ubuntu) instalación por paquete del sistema:
  sudo apt update
  sudo apt install -y python3-opencv python3-numpy

Cómo probar / ejecutar
1. Asegúrate de que la imagen de entrada exista en:
   TrabajoPractico3/Hit1/inputSobel.jpeg
   (si no existe, crear la imagen ahi con ese nombre)

2. Ejecuta desde la raíz del proyecto:
    python3 TrabajoPractico3/Hit1/etapa1/sobel.py

## Pruebas (pytest)
Para ejecutar los tests unitarios de la lógica de procesamiento:
1. Instalar pytest (si no está instalado):
   `python3 -m pip install pytest`
2. Ejecutar desde la raíz del proyecto:
   `python3 -m pytest TrabajoPractico3/Hit1/etapa1/test_sobel.py`

Salida esperada
- Archivo generado:
  TrabajoPractico3/Hit1/etapa1/outputSobel.png

Solución de problemas rápida
- Si aparece `ModuleNotFoundError: No module named 'cv2'` -> instala dependencias con pip o apt (ver arriba).
- Si el script indica que no encontró la imagen de entrada, verifica la ruta y el nombre: `inputSobel.jpeg` (en la carpeta `Hit1`, una carpeta arriba de `etapa1`).

Resultado obtenido:
La ejecucion del proceso de manera centralizada demoro 0.634 segundos en finalizar con exito (aplicar la mascara de sobel y crear la imagen de output) la primera vez.

Al volver a realizar la prueba, el proceso demoro 0.043 segundos (no por el algoritmo en si, sino por la cache).
