FROM python:3.10-slim

WORKDIR /app

COPY TrabajoPractico2/Hit3 .
COPY TrabajoPractico2/common /app/common
COPY api /app/api

RUN pip install fastapi uvicorn docker requests

EXPOSE 8000

# Montar el socket de Docker para acceso al daemon del host
VOLUME /var/run/docker.sock

CMD ["uvicorn", "servicio_tarea:app", "--host", "0.0.0.0", "--port", "8000"]