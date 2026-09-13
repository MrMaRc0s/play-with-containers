import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import SQLAlchemyError

from app.consumers.billing_consumer import create_message_handler, parse_order


VALID_MESSAGE = (
    b'{"user_id":"20","number_of_items":"99","total_amount":"250"}'
)


class ParseOrderTests(unittest.TestCase):
    def test_parses_subject_payload(self):
        self.assertEqual(
            parse_order(VALID_MESSAGE),
            {
                "user_id": 20,
                "number_of_items": 99,
                "total_amount": Decimal("250"),
            },
        )

    def test_rejects_invalid_payloads(self):
        invalid_messages = (
            b"not-json",
            b"[]",
            b'{"user_id":true,"number_of_items":1,"total_amount":1}',
            b'{"user_id":1.5,"number_of_items":1,"total_amount":1}',
            b'{"user_id":1,"number_of_items":0,"total_amount":1}',
            b'{"user_id":1,"number_of_items":1,"total_amount":-1}',
        )

        for message in invalid_messages:
            with self.subTest(message=message):
                with self.assertRaises(ValueError):
                    parse_order(message)


class MessageHandlerTests(unittest.TestCase):
    def setUp(self):
        self.channel = MagicMock()
        self.method = SimpleNamespace(delivery_tag=7)
        self.session_factory = MagicMock()
        self.session = self.session_factory.begin.return_value.__enter__.return_value

    @patch("app.consumers.billing_consumer.Order")
    def test_acknowledges_only_after_database_commit(self, order_class):
        order_class.return_value.id = 42
        events = []
        self.session.flush.side_effect = lambda: events.append("flush")
        self.session_factory.begin.return_value.__exit__.side_effect = (
            lambda *_args: events.append("commit")
        )
        self.channel.basic_ack.side_effect = lambda **_kwargs: events.append("ack")

        handler = create_message_handler(self.session_factory)
        handler(self.channel, self.method, None, VALID_MESSAGE)

        self.session.add.assert_called_once_with(order_class.return_value)
        self.channel.basic_nack.assert_not_called()
        self.channel.basic_ack.assert_called_once_with(delivery_tag=7)
        self.assertEqual(events, ["flush", "commit", "ack"])

    def test_discards_invalid_message_without_acknowledging(self):
        handler = create_message_handler(self.session_factory)
        handler(self.channel, self.method, None, b"not-json")

        self.session_factory.begin.assert_not_called()
        self.channel.basic_ack.assert_not_called()
        self.channel.basic_nack.assert_called_once_with(
            delivery_tag=7,
            requeue=False,
        )

    def test_requeues_message_when_database_operation_fails(self):
        self.session.add.side_effect = SQLAlchemyError("database unavailable")

        handler = create_message_handler(self.session_factory)
        handler(self.channel, self.method, None, VALID_MESSAGE)

        self.channel.basic_ack.assert_not_called()
        self.channel.basic_nack.assert_called_once_with(
            delivery_tag=7,
            requeue=True,
        )


if __name__ == "__main__":
    unittest.main()
