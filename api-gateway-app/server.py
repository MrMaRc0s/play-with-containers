import logging
import os

from app import create_app
from app.config.settings import load_settings


LOGGER = logging.getLogger(__name__)


def configure_logging() -> None:
    handlers = [logging.StreamHandler()]

    log_dir = os.getenv("GATEWAY_LOG_DIR")
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        handlers.append(logging.FileHandler(os.path.join(log_dir, "gateway.log")))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def main() -> None:
    configure_logging()

    settings = load_settings()
    app = create_app(settings)

    LOGGER.info("API Gateway is listening on port %s", settings.gateway_port)
    app.run(host="0.0.0.0", port=settings.gateway_port)


if __name__ == "__main__":
    main()
