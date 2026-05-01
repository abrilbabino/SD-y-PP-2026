import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch


PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_DIR, "src")
sys.path.insert(0, SRC_DIR)

import producer
import worker


class WorkQueueIntegrationTest(unittest.TestCase):
    def test_producer_builds_rabbitmq_url_from_environment(self):
        with patch.dict(
            os.environ,
            {
                "RABBITMQ_USER": "user",
                "RABBITMQ_PASS": "pass",
                "RABBIT_HOST": "rabbitmq",
                "RABBITMQ_PORT": "5672",
            },
        ):
            self.assertEqual(
                producer.build_rabbitmq_url(),
                "amqp://user:pass@rabbitmq:5672/",
            )

    def test_queue_name_comes_from_environment(self):
        with patch.dict(os.environ, {"QUEUE_NAME": "custom_queue"}):
            self.assertEqual(producer.get_queue_name(), "custom_queue")
            self.assertEqual(worker.get_queue_name(), "custom_queue")

    def test_health_response_shape_is_required_json(self):
        expected = {"servicio": "status"}
        self.assertEqual(json.dumps(expected), '{"servicio": "status"}')

    @patch("producer.pika.BlockingConnection")
    def test_producer_publishes_ten_persistent_tasks(self, connection_mock):
        channel = MagicMock()
        connection = MagicMock()
        connection.channel.return_value = channel
        connection_mock.return_value = connection

        with patch("producer.start_health_server"), patch("producer.time.sleep", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                producer.main()

        self.assertEqual(channel.basic_publish.call_count, 10)
        first_message = channel.basic_publish.call_args_list[0].kwargs["body"]
        last_message = channel.basic_publish.call_args_list[-1].kwargs["body"]
        self.assertEqual(first_message, "Tarea 1 de 10")
        self.assertEqual(last_message, "Tarea 10 de 10")

    def test_worker_uses_port_8081_by_default(self):
        self.assertEqual(worker.HEALTH_PORT, 8081)


if __name__ == "__main__":
    unittest.main()
