import logging
import signal

import app.models  # Registers SQLAlchemy models before schema creation.
from app.config.database import (
    create_database_engine,
    create_schema,
    create_session_factory,
)
from app.config.rabbitmq import create_rabbitmq_connection
from app.config.settings import load_settings
from app.consumers import create_message_handler


LOGGER = logging.getLogger(__name__)


def request_shutdown(_signal_number, _frame) -> None:
    raise KeyboardInterrupt


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    settings = load_settings()
    engine = create_database_engine(settings)
    connection = None
    channel = None

    signal.signal(signal.SIGTERM, request_shutdown)

    try:
        create_schema(engine)
        session_factory = create_session_factory(engine)
        connection, channel = create_rabbitmq_connection(settings)
        channel.basic_consume(
            queue=settings.rabbitmq_queue,
            on_message_callback=create_message_handler(session_factory),
            auto_ack=False,
        )

        LOGGER.info(
            "Billing consumer is waiting on queue %s",
            settings.rabbitmq_queue,
        )
        channel.start_consuming()
    except KeyboardInterrupt:
        LOGGER.info("Stopping Billing consumer")
    finally:
        if channel is not None and channel.is_open:
            channel.stop_consuming()
        if connection is not None and connection.is_open:
            connection.close()
        engine.dispose()


if __name__ == "__main__":
    main()
