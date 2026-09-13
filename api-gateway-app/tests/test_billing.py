import json
import unittest
from unittest.mock import MagicMock, patch

from pika.exceptions import AMQPConnectionError

from app import create_app
from app.config.settings import Settings


SETTINGS = Settings(
    gateway_port=3000,
    inventory_api_url="http://inventory:8080",
    rabbitmq_host="rabbitmq",
    rabbitmq_port=5672,
    rabbitmq_user="user",
    rabbitmq_password="password",
    rabbitmq_queue="billing_queue",
)


class BillingTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app(SETTINGS).test_client()

    @patch("app.config.rabbitmq.pika.BlockingConnection")
    def test_publishes_a_persistent_message_to_the_durable_queue(self, mock_connection_cls):
        mock_channel = MagicMock()
        mock_connection_cls.return_value.channel.return_value = mock_channel

        response = self.client.post(
            "/api/billing",
            json={"user_id": 1, "number_of_items": 2, "total_amount": 9.99},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"message": "Message posted"})

        mock_channel.queue_declare.assert_called_once_with(
            queue="billing_queue", durable=True
        )
        _, publish_kwargs = mock_channel.basic_publish.call_args
        self.assertEqual(publish_kwargs["routing_key"], "billing_queue")
        self.assertEqual(
            json.loads(publish_kwargs["body"]),
            {"user_id": 1, "number_of_items": 2, "total_amount": 9.99},
        )
        self.assertEqual(publish_kwargs["properties"].delivery_mode, 2)
        mock_connection_cls.return_value.close.assert_called_once()

    def test_rejects_a_non_json_body(self):
        response = self.client.post(
            "/api/billing", data="not-json", content_type="text/plain"
        )

        self.assertEqual(response.status_code, 400)

    @patch("app.config.rabbitmq.pika.BlockingConnection")
    def test_returns_service_error_when_rabbitmq_is_unavailable(self, mock_connection_cls):
        mock_connection_cls.side_effect = AMQPConnectionError("refused")

        response = self.client.post("/api/billing", json={"user_id": 1})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {"error": "Billing queue unavailable"})


if __name__ == "__main__":
    unittest.main()
