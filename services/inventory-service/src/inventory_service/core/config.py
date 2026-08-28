from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[5]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")
    INVENTORY_DB_URL: str
    INVENTORY_DB_USER: str
    INVENTORY_DB_PASSWORD: str
    INVENTORY_DB_NAME: str
    INVENTORY_DB_HOST: str
    INVENTORY_DB_PORT: int
    RABBITMQ_URL: str
    INVENTORY_RESERVATION_TTL_SECONDS: int = 900
    DB_ECHO: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
