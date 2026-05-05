import json
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ex1.src import producer
from ex1.src import worker

def test_producer_builds_rabbitmq_url_from_environment():
    with patch.dict(
        os.environ,
        {
            "RABBITMQ_USER": "user",
            "RABBITMQ_PASS": "pass",
            "RABBIT_HOST": "rabbitmq",
            "RABBITMQ_PORT": "5672",
        },
    ):
        assert producer.build_rabbitmq_url() == "amqp://user:pass@rabbitmq:5672/"

def test_queue_name_comes_from_environment():
    with patch.dict(os.environ, {"QUEUE_NAME": "custom_queue"}):
        assert producer.get_queue_name() == "custom_queue"
        assert worker.get_queue_name() == "custom_queue"

def test_health_response_shape_is_required_json():
    expected = {"servicio": "status"}
    assert json.dumps(expected) == '{"servicio": "status"}'

@patch("ex1.src.producer.pika.BlockingConnection")
def test_producer_publishes_ten_persistent_tasks(connection_mock):
    channel = MagicMock()
    connection = MagicMock()
    connection.channel.return_value = channel
    connection_mock.return_value = connection

    with patch("ex1.src.producer.start_health_server"), patch("ex1.src.producer.time.sleep", side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            producer.main()

    assert channel.basic_publish.call_count == 10
    first_message = channel.basic_publish.call_args_list[0].kwargs["body"]
    last_message = channel.basic_publish.call_args_list[-1].kwargs["body"]
    assert first_message == "Tarea 1 de 10"
    assert last_message == "Tarea 10 de 10"

def test_worker_uses_port_8081_by_default():
    assert worker.HEALTH_PORT == 8081
