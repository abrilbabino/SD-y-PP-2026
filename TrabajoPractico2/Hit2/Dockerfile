FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn

EXPOSE 5000

VOLUME /var/run/docker.sock

CMD ["uvicorn", "servicio_tarea:app", "--host", "0.0.0.0", "--port", "5000"]