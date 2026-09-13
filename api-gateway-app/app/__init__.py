"""API Gateway application package."""
from flask import Flask

from app.billing import create_billing_blueprint
from app.config.settings import Settings
from app.proxy import create_inventory_proxy_blueprint


def create_app(settings: Settings) -> Flask:
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.register_blueprint(create_inventory_proxy_blueprint(settings))
    app.register_blueprint(create_billing_blueprint(settings))
    return app
