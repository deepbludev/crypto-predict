from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from domain.candles import CandleTimeframe


class EmissionMode(str, Enum):
    """The mode of emission of candles.

    LIVE: emit partial candles as soon as a new trade is received
    FULL: emit full candles only after the window is closed
    """

    LIVE = "LIVE"
    FULL = "FULL"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/candles/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="candles_",
    )

    broker_address: str = "localhost:19092"
    consumer_group: str = "cg_candles"
    input_topic: str = "trades"
    output_topic: str = "candles"
    timeframe: CandleTimeframe = CandleTimeframe.tf_1m
    emission_mode: EmissionMode = EmissionMode.LIVE


@lru_cache()
def candles_settings() -> Settings:
    return Settings()
