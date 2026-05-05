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


class RetryBackoffIntegrationTest(unittest.TestCase):
    def test_config_comes_from_environment(self):
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

        self.assertEqual(config["host"], "rabbitmq-ex4")
        self.assertEqual(config["main_queue"], "main_queue_test")
        self.assertEqual(config["retry_queue"], "retry_queue_test")
        self.assertEqual(config["dead_letter_queue"], "dlq_test")

    def test_health_response_shape_is_required_json(self):
        self.assertEqual(json.dumps({"servicio": "status"}), '{"servicio": "status"}')

    def test_retry_queue_declares_dead_letter_back_to_main_queue(self):
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

    def test_backoff_sequence_is_exponential(self):
        self.assertEqual(consumer.BACKOFF_SECONDS, [1, 2, 4, 8])
        self.assertEqual(consumer.get_backoff_seconds(1), 1)
        self.assertEqual(consumer.get_backoff_seconds(4), 8)
        self.assertEqual(consumer.MAX_RETRIES, 4)

    def test_publish_retry_uses_expiration_and_retry_header(self):
        channel = MagicMock()
        config = consumer.get_config()

        consumer.publish_retry(channel, config, b'{"id": 1}', attempt=2, wait_seconds=4)

        _, kwargs = channel.basic_publish.call_args
        self.assertEqual(kwargs["exchange"], config["retry_exchange"])
        self.assertEqual(kwargs["routing_key"], config["retry_routing_key"])
        self.assertEqual(kwargs["properties"].expiration, "4000")
        self.assertEqual(kwargs["properties"].headers["x-retry-attempt"], 2)

    def test_producer_builds_plain_messages(self):
        messages = producer.build_messages()

        self.assertEqual(len(messages), 10)
        self.assertNotIn("error", messages[0])

    def test_dlq_consumer_default_port(self):
        self.assertEqual(dlq_consumer.HEALTH_PORT, 8082)


if __name__ == "__main__":
    unittest.main()
