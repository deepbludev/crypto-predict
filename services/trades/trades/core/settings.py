from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="trades_",
    )

    broker_address: str = "localhost:19092"
    topic: str = "trades"
    pairs: list[str] = ["XRP/USD"]


@lru_cache()
def trades_settings() -> Settings:
    return Settings()