"""Inventory application package."""
from flask import Flask

from app.routes.movies import create_movies_blueprint


def create_app(session_factory) -> Flask:
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.register_blueprint(
        create_movies_blueprint(session_factory), url_prefix="/api/movies"
    )
    return app
