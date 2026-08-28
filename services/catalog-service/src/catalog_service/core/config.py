from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[5]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    CATALOG_DB_URL: str
    CATALOG_DB_USER: str
    CATALOG_DB_PASSWORD: str
    CATALOG_DB_NAME: str
    CATALOG_DB_HOST: str
    CATALOG_DB_PORT: int
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    DB_ECHO: bool = False
    TESTING: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore


settings = get_settings()
