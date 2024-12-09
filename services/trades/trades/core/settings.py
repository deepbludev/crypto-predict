from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from domain.trades import Symbol


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/trades/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="trades_",
    )

    broker_address: str = "localhost:19092"
    consumer_group: str = "cg_trades"
    topic: str = "trades"
    symbols: list[Symbol] = [Symbol.XRPUSD]


@lru_cache()
def trades_settings() -> Settings:
    return Settings()
