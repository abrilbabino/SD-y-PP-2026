FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ROLE=worker

RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

WORKDIR /app

RUN pip install --no-cache-dir pika

COPY --chown=appuser:appuser src/ ./src/

USER appuser

CMD ["sh", "-c", "python -u src/${APP_ROLE}.py"]
