# Etapa 2 — Sobel (distribuido, Master-Worker con RabbitMQ)

Arquitectura
- Master (container): lee `TrabajoPractico3/Hit1/inputSobel.jpeg`, lo divide en N chunks (splitter),
  publica cada chunk como tarea en la cola `sobel_tasks`.
- Workers (cada uno en su contenedor): consumen de `sobel_tasks`, aplican Sobel al chunk y publican
  el resultado en `sobel_results`.
- Master: consume `sobel_results` (joiner), espera N resultados, los une y escribe `etapa2/outputSobel.png`.

IMPORTANTE — Sin tolerancia a fallos (Etapa 2)
- En esta etapa NO se implementa tolerancia a fallos ni reintentos. Es decir:
  - Las colas y los mensajes no son persistentes.
  - Los consumidores se configuran con auto_ack=True; si un worker falla mientras procesa, ese trabajo se pierde.
  - La reentrega de mensajes, DLQ o reintentos se dejarán para la Etapa 3.
- Este diseño simplifica la implementación y permite enfocarse en el particionado, procesamiento distribuido y ensamblado
  sin manejar recuperación de errores.

Comunicación
- RabbitMQ actúa como broker. Se usan 2 colas (no durables en esta etapa):
  - sobel_tasks: tareas (chunk + metadatos).
  - sobel_results: resultados (chunk procesado + metadatos).
- Ventajas en Etapa 2: separación de responsabilidades y escalado de workers.
- Limitaciones en Etapa 2: no hay garantía de entrega ni tolerancia a fallos; considerar estas mejoras en la Etapa 3.

Cómo probar con Docker Compose
1. Colocar `inputSobel.jpeg` en `TrabajoPractico3/Hit1/` (una carpeta arriba de `etapa2`).
2. Ir a la carpeta etapa2:
   cd TrabajoPractico3/Hit1/etapa2
3. Construir y levantar (ejemplo con 4 workers):
   docker-compose up --build --scale worker=4
   - El servicio `master` publica 4 tareas y terminará cuando reciba los 4 resultados.
   - Los archivos de salida estarán en `TrabajoPractico3/Hit1/etapa2/outputSobel.png`.

Comandos alternativos (para ejecutar master local y solo los workers en docker)
1. Levantar RabbitMQ:
   docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
2. Levantar N workers:
   docker build -t sobel-worker .
   docker run -e RABBIT_HOST=host.docker.internal sobel-worker python3 worker.py
3. Ejecutar master localmente:
    RABBIT_HOST=localhost python3 master.py --workers 4

## Pruebas (pytest)
Para ejecutar los tests unitarios de la lógica distribuida (splitting, joining, etc.):
1. Instalar pytest (si no está instalado):
   `python3 -m pip install pytest`
2. Ejecutar desde la raíz del proyecto:
   `python3 -m pytest TrabajoPractico3/Hit1/etapa2/tests/test_logic.py`

Notas sobre RabbitMQ en este patrón
- Usamos colas y basic_ack para el procesamiento, pero sin garantía de entrega.
- Si un worker cae mientras procesa, el mensaje será perdido y no reencolado.
- Considerar mejoras para tolerancia a fallos en la Etapa 3.

Archivos importantes
- master.py, worker.py, Dockerfile, docker-compose.yml, requirements.txt

- Resultado de la ejecucion:
<img width="567" height="139" alt="Imagen1" src="https://github.com/user-attachments/assets/b90613df-0704-4637-b2c8-4c03bf94ece0" />



