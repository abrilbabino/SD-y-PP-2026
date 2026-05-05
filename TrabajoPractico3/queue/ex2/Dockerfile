FROM python:3.11-slim

# Evitar la escritura de bytecodes y forzar flush de logs a STDOUT
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

WORKDIR /app

# Copiar requirements (se asume que el contexto de build es la raíz TrabajoPractico3/)
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del ejercicio a /app/src/
COPY --chown=appuser:appuser TrabajoPractico3/queue/ex2/src/ ./src/

USER appuser
