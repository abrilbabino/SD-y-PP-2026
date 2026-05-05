FROM python:3.11-slim
WORKDIR /app

# dependencias del sistema necesarias para OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# copiar e instalar dependencias python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copiar el contenido de la carpeta etapa3 al path esperado por los manifests
COPY . /app/etapa3
WORKDIR /app/etapa3

# por defecto ejecutará python3 <script> (command/entrypoint se define en manifests)
ENTRYPOINT ["python3"]
