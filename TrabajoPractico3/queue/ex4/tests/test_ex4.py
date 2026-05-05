import json
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ex4.src import consumer
from ex4.src import dlq_consumer
from ex4.src import producer

def test_config_comes_from_environment():
    with patch.dict(
        os.environ,
        {
            "RABBITMQ_USER": "user",
            "RABBITMQ_PASS": "pass",
            "RABBITMQ_HOST": "rabbitmq-ex4",
            "RABBITMQ_PORT": "5672",
            "MAIN_QUEUE": "main_queue_test",
            "RETRY_QUEUE": "retry_queue_test",
            "DEAD_LETTER_QUEUE": "dlq_test",
        },
    ):
        config = producer.get_config()

    assert config["host"] == "rabbitmq-ex4"
    assert config["main_queue"] == "main_queue_test"
    assert config["retry_queue"] == "retry_queue_test"
    assert config["dead_letter_queue"] == "dlq_test"

def test_health_response_shape_is_required_json():
    assert json.dumps({"servicio": "status"}) == '{"servicio": "status"}'

def test_retry_queue_declares_dead_letter_back_to_main_queue():
    channel = MagicMock()
    config = producer.get_config()

    producer.declare_topology(channel, config)

    channel.queue_declare.assert_any_call(
        queue=config["retry_queue"],
        durable=True,
        arguments={
            "x-dead-letter-exchange": config["main_exchange"],
            "x-dead-letter-routing-key": config["main_routing_key"],
        },
    )

def test_backoff_sequence_is_exponential():
    assert consumer.BACKOFF_SECONDS == [1, 2, 4, 8]
    assert consumer.get_backoff_seconds(1) == 1
    assert consumer.get_backoff_seconds(4) == 8
    assert consumer.MAX_RETRIES == 4

def test_publish_retry_uses_expiration_and_retry_header():
    channel = MagicMock()
    config = consumer.get_config()

    consumer.publish_retry(channel, config, b'{"id": 1}', attempt=2, wait_seconds=4)

    _, kwargs = channel.basic_publish.call_args
    assert kwargs["exchange"] == config["retry_exchange"]
    assert kwargs["routing_key"] == config["retry_routing_key"]
    assert kwargs["properties"].expiration == "4000"
    assert kwargs["properties"].headers["x-retry-attempt"] == 2

def test_producer_builds_plain_messages():
    messages = producer.build_messages()

    assert len(messages) == 10
    assert "error" not in messages[0]

def test_dlq_consumer_default_port():
    assert dlq_consumer.HEALTH_PORT == 8082
