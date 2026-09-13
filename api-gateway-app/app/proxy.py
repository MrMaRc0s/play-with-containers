import logging

import requests
from flask import Blueprint, Response, request

from app.config.settings import Settings


LOGGER = logging.getLogger(__name__)

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "content-length",
    "content-encoding",
}


def create_inventory_proxy_blueprint(settings: Settings) -> Blueprint:
    inventory_proxy_blueprint = Blueprint("inventory_proxy", __name__)

    def forward(movie_id=None):
        target_url = f"{settings.inventory_api_url}/api/movies"
        if movie_id is not None:
            target_url = f"{target_url}/{movie_id}"

        try:
            upstream_response = requests.request(
                method=request.method,
                url=target_url,
                params=request.args,
                data=request.get_data(),
                headers={
                    "Content-Type": request.headers.get(
                        "Content-Type", "application/json"
                    )
                },
                timeout=10,
            )
        except requests.RequestException as error:
            LOGGER.error("Could not reach Inventory API: %s", error)
            return {"error": "Inventory API unavailable"}, 503

        response_headers = [
            (name, value)
            for name, value in upstream_response.headers.items()
            if name.lower() not in HOP_BY_HOP_HEADERS
        ]

        return Response(
            upstream_response.content,
            status=upstream_response.status_code,
            headers=response_headers,
        )

    @inventory_proxy_blueprint.route("/api/movies", methods=["GET", "POST", "DELETE"])
    def proxy_collection():
        return forward()

    @inventory_proxy_blueprint.route(
        "/api/movies/<path:movie_id>", methods=["GET", "PUT", "DELETE"]
    )
    def proxy_item(movie_id):
        return forward(movie_id)

    return inventory_proxy_blueprint
