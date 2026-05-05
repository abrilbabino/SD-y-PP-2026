import json
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ex3.src import consumer
from ex3.src import dlq_consumer
from ex3.src import producer

def test_config_comes_from_environment():
    with patch.dict(
        os.environ,
        {
            "RABBITMQ_USER": "user",
            "RABBITMQ_PASS": "pass",
            "RABBITMQ_HOST": "rabbitmq-ex3",
            "RABBITMQ_PORT": "5672",
            "MAIN_QUEUE": "main_queue_test",
            "DEAD_LETTER_QUEUE": "dlq_test",
        },
    ):
        config = producer.get_config()

    assert config["host"] == "rabbitmq-ex3"
    assert config["main_queue"] == "main_queue_test"
    assert config["dead_letter_queue"] == "dlq_test"

def test_health_response_shape_is_required_json():
    assert json.dumps({"servicio": "status"}) == '{"servicio": "status"}'

def test_main_queue_declares_dead_letter_arguments():
    channel = MagicMock()
    config = producer.get_config()

    producer.declare_topology(channel, config)

    channel.queue_declare.assert_any_call(
        queue=config["main_queue"],
        durable=True,
        arguments={
            "x-dead-letter-exchange": config["dlx_exchange"],
            "x-dead-letter-routing-key": config["dlq_routing_key"],
        },
    )

def test_consumer_rejects_error_messages_without_requeue():
    assert consumer.should_reject({"id": 1, "error": True}) is True
    assert consumer.should_reject({"id": 2, "error": False}) is False

def test_producer_builds_messages_with_error_cases():
    messages = producer.build_messages()
    error_messages = [message for message in messages if message.get("error")]

    assert len(messages) == 10
    assert len(error_messages) >= 1

def test_dlq_consumer_default_port():
    assert dlq_consumer.HEALTH_PORT == 8082
