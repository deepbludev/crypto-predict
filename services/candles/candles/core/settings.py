from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from domain.candles import CandleWindowSize


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/candles/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="candles_",
    )

    broker_address: str = "localhost:19092"
    consumer_group: str = "candles_consumer_group"
    input_topic: str = "trades"
    output_topic: str = "candles"
    window_size: CandleWindowSize = CandleWindowSize.CANDLE_1m


@lru_cache()
def candles_settings() -> Settings:
    return Settings()
