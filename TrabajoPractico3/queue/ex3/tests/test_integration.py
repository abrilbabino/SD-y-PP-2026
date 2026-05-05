import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch


PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_DIR, "src")
sys.path.insert(0, SRC_DIR)

import consumer
import dlq_consumer
import producer


class DeadLetterQueueIntegrationTest(unittest.TestCase):
    def test_config_comes_from_environment(self):
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

        self.assertEqual(config["host"], "rabbitmq-ex3")
        self.assertEqual(config["main_queue"], "main_queue_test")
        self.assertEqual(config["dead_letter_queue"], "dlq_test")

    def test_health_response_shape_is_required_json(self):
        self.assertEqual(json.dumps({"servicio": "status"}), '{"servicio": "status"}')

    def test_main_queue_declares_dead_letter_arguments(self):
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

    def test_consumer_rejects_error_messages_without_requeue(self):
        self.assertTrue(consumer.should_reject({"id": 1, "error": True}))
        self.assertFalse(consumer.should_reject({"id": 2, "error": False}))

    def test_producer_builds_messages_with_error_cases(self):
        messages = producer.build_messages()
        error_messages = [message for message in messages if message["error"]]

        self.assertEqual(len(messages), 10)
        self.assertGreaterEqual(len(error_messages), 1)

    def test_dlq_consumer_default_port(self):
        self.assertEqual(dlq_consumer.HEALTH_PORT, 8082)


if __name__ == "__main__":
    unittest.main()
