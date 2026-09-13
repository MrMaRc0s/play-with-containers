import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_ENV_FILE = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(ROOT_ENV_FILE, override=False)


def require_environment_variable(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def require_port(name: str) -> int:
    value = require_environment_variable(name)
    try:
        port = int(value)
    except ValueError as error:
        raise RuntimeError(f"{name} must be an integer") from error

    if not 1 <= port <= 65535:
        raise RuntimeError(f"{name} must be between 1 and 65535")
    return port


@dataclass(frozen=True)
class Settings:
    inventory_port: int
    inventory_db_host: str
    inventory_db_port: int
    inventory_db_name: str
    inventory_db_user: str
    inventory_db_password: str


def load_settings() -> Settings:
    return Settings(
        inventory_port=require_port("INVENTORY_PORT"),
        inventory_db_host=require_environment_variable("INVENTORY_DB_HOST"),
        inventory_db_port=require_port("INVENTORY_DB_PORT"),
        inventory_db_name=require_environment_variable("INVENTORY_DB_NAME"),
        inventory_db_user=require_environment_variable("INVENTORY_DB_USER"),
        inventory_db_password=require_environment_variable("INVENTORY_DB_PASSWORD"),
    )
