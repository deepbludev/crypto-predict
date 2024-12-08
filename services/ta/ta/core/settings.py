from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from domain.candles import CandleWindowSize


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/ta/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="ta_",
    )

    broker_address: str = "localhost:19092"
    consumer_group: str = "ta"
    input_topic: str = "candles"
    output_topic: str = "ta"
    candle_window_size: CandleWindowSize = CandleWindowSize.CANDLE_1m


@lru_cache()
def ta_settings() -> Settings:
    return Settings()
