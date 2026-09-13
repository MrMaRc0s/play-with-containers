import unittest
from unittest.mock import MagicMock, patch

import requests

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


class ProxyTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app(SETTINGS).test_client()

    @patch("app.proxy.requests.request")
    def test_forwards_query_string_and_upstream_body(self, mock_request):
        mock_request.return_value = MagicMock(
            status_code=200,
            content=b'[{"id":"1","title":"Inception","description":"x"}]',
            headers={"Content-Type": "application/json"},
        )

        response = self.client.get("/api/movies?title=incep")

        mock_request.assert_called_once()
        call = mock_request.call_args.kwargs
        self.assertEqual(call["method"], "GET")
        self.assertEqual(call["url"], "http://inventory:8080/api/movies")
        self.assertEqual(call["params"]["title"], "incep")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["title"], "Inception")

    @patch("app.proxy.requests.request")
    def test_forwards_movie_id_and_method(self, mock_request):
        mock_request.return_value = MagicMock(
            status_code=404,
            content=b'{"error":"Movie not found"}',
            headers={"Content-Type": "application/json"},
        )

        response = self.client.delete("/api/movies/42")

        call = mock_request.call_args.kwargs
        self.assertEqual(call["method"], "DELETE")
        self.assertEqual(call["url"], "http://inventory:8080/api/movies/42")
        self.assertEqual(response.status_code, 404)

    @patch("app.proxy.requests.request")
    def test_returns_service_error_when_inventory_is_unreachable(self, mock_request):
        mock_request.side_effect = requests.ConnectionError("refused")

        response = self.client.get("/api/movies")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {"error": "Inventory API unavailable"})


if __name__ == "__main__":
    unittest.main()
