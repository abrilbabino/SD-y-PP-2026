FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ROLE=producer

WORKDIR /app

RUN pip install --no-cache-dir pika

COPY src/ ./src/

CMD ["sh", "-c", "python -u src/${APP_ROLE}.py"]
