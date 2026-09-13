from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config.settings import Settings


class Base(DeclarativeBase):
    """Base class for Billing database models."""


def create_database_engine(settings: Settings):
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.billing_db_user,
        password=settings.billing_db_password,
        host=settings.billing_db_host,
        port=settings.billing_db_port,
        database=settings.billing_db_name,
    )
    return create_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_schema(engine) -> None:
    Base.metadata.create_all(engine)
