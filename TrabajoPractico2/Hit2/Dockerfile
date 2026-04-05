FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn docker requests

EXPOSE 8000
EXPOSE 5000

# por defecto corre el SERVER
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]