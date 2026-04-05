FROM python:3.10-slim

WORKDIR /app

COPY servicio_tarea.py .

RUN pip install fastapi uvicorn

EXPOSE 5000

CMD ["uvicorn", "servicio_tarea:app", "--host", "0.0.0.0", "--port", "8000"]