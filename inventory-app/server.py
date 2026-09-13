import logging

from app import create_app
from app.config.database import (
    create_database_engine,
    create_schema,
    create_session_factory,
)
from app.config.settings import load_settings


LOGGER = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    settings = load_settings()
    engine = create_database_engine(settings)
    create_schema(engine)
    session_factory = create_session_factory(engine)

    app = create_app(session_factory)

    LOGGER.info("Inventory API is listening on port %s", settings.inventory_port)
    app.run(host="0.0.0.0", port=settings.inventory_port)


if __name__ == "__main__":
    main()
