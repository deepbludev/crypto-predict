from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from domain.candles import CandleTimeframe


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/ta/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="ta_",
    )

    broker_address: str = "localhost:19092"
    consumer_group: str = "cg_ta"
    input_topic: str = "candles"
    output_topic: str = "ta"
    candle_timeframe: CandleTimeframe = CandleTimeframe.tf_1m
    max_candles_in_state: int = 60


@lru_cache()
def ta_settings() -> Settings:
    return Settings()
