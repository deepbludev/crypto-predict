from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from domain.candles import CandleTimeframe, EmissionMode
from domain.trades import TradesIngestionMode


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
    trade_ingestion_mode: TradesIngestionMode = TradesIngestionMode.LIVE


@lru_cache()
def candles_settings() -> Settings:
    return Settings()
