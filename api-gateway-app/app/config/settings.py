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
    gateway_port: int
    inventory_api_url: str
    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_user: str
    rabbitmq_password: str
    rabbitmq_queue: str


def load_settings() -> Settings:
    return Settings(
        gateway_port=require_port("GATEWAY_PORT"),
        inventory_api_url=require_environment_variable("INVENTORY_API_URL").rstrip("/"),
        rabbitmq_host=require_environment_variable("RABBITMQ_HOST"),
        rabbitmq_port=require_port("RABBITMQ_PORT"),
        rabbitmq_user=require_environment_variable("RABBITMQ_USER"),
        rabbitmq_password=require_environment_variable("RABBITMQ_PASSWORD"),
        rabbitmq_queue=require_environment_variable("RABBITMQ_QUEUE"),
    )
