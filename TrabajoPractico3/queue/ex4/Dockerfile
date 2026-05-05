# Stage 1: Build Stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Crear usuario temporal para el build
RUN groupadd -g 1000 builduser && \
    useradd -u 1000 -g builduser -s /bin/bash -m builduser

USER builduser
WORKDIR /home/builduser/build

# Copiar requirements desde la raíz del contexto con el owner correcto
COPY --chown=builduser:builduser requirements.txt .
# Instalar dependencias en ~/.local sin privilegios de root
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime Stage
FROM python:3.11-slim

# Variables de entorno originales y actualización del PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ROLE=producer
ENV PATH=/home/appuser/.local/bin:$PATH

# Creación de usuario no-root
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

WORKDIR /app

# Copiado selectivo de dependencias desde el Stage 1
COPY --from=builder --chown=appuser:appuser /home/builduser/.local /home/appuser/.local

# Copiado del código fuente del ejercicio
COPY --chown=appuser:appuser TrabajoPractico3/queue/ex4/src/ ./src/

USER appuser

CMD ["sh", "-c", "python -u src/${APP_ROLE}.py"]
