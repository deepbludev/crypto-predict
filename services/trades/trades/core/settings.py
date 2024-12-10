from datetime import datetime
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

    # kraken
    kraken_ws_endpoint: str = "wss://ws.kraken.com/v2"
    kraken_rest_endpoint: str = "https://api.kraken.com/0/public/Trades"
    kraken_backfill_trades_since: datetime | None = None  # None means no backfill


@lru_cache()
def trades_settings() -> Settings:
    return Settings()
