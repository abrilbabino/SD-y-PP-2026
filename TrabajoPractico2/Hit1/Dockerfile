FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn

EXPOSE 5000

# Montar el socket de Docker para acceso al daemon del host
VOLUME /var/run/docker.sock

CMD ["uvicorn", "servicio_tarea:app", "--host", "0.0.0.0", "--port", "5000"]