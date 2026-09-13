import json
import logging
from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import SQLAlchemyError

from app.models import Order


LOGGER = logging.getLogger(__name__)


def parse_positive_integer(value, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive integer")

    try:
        parsed_value = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be a positive integer") from error

    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"{field_name} must be a positive integer")
    if parsed_value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")

    return parsed_value


def parse_non_negative_amount(value) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("total_amount must be a non-negative number")

    try:
        parsed_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError("total_amount must be a non-negative number") from error

    if not parsed_value.is_finite() or parsed_value < 0:
        raise ValueError("total_amount must be a non-negative number")

    return parsed_value


def parse_order(body: bytes) -> dict:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("message body must be valid UTF-8 JSON") from error

    if not isinstance(payload, dict):
        raise ValueError("message body must be a JSON object")

    return {
        "user_id": parse_positive_integer(payload.get("user_id"), "user_id"),
        "number_of_items": parse_positive_integer(
            payload.get("number_of_items"),
            "number_of_items",
        ),
        "total_amount": parse_non_negative_amount(payload.get("total_amount")),
    }


def create_message_handler(session_factory):
    def handle_message(channel, method, _properties, body: bytes) -> None:
        try:
            order_data = parse_order(body)
        except ValueError as error:
            LOGGER.error("Rejected invalid billing message: %s", error)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        try:
            with session_factory.begin() as session:
                order = Order(**order_data)
                session.add(order)
                session.flush()
                order_id = order.id
        except SQLAlchemyError as error:
            LOGGER.error("Billing database operation failed: %s", error)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return

        channel.basic_ack(delivery_tag=method.delivery_tag)
        LOGGER.info("Processed billing order %s", order_id)

    return handle_message
