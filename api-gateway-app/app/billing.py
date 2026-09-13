import json
import logging

from flask import Blueprint, jsonify, request
from pika.exceptions import AMQPError

from app.config.rabbitmq import publish_billing_message
from app.config.settings import Settings


LOGGER = logging.getLogger(__name__)


def create_billing_blueprint(settings: Settings) -> Blueprint:
    billing_blueprint = Blueprint("billing", __name__)

    @billing_blueprint.post("/api/billing")
    def publish():
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({"error": "Request body must be valid JSON"}), 400

        payload = json.dumps(body).encode("utf-8")

        try:
            publish_billing_message(settings, payload)
        except AMQPError as error:
            LOGGER.error("Could not queue billing request: %s", error)
            return jsonify({"error": "Billing queue unavailable"}), 503

        return jsonify({"message": "Message posted"}), 200

    return billing_blueprint
