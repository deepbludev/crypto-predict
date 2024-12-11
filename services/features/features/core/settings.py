from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from domain.trades import TradeIngestionMode


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/features/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="features_",
    )

    # broker settings
    broker_address: str = "localhost:19092"
    consumer_group: str = "cg_features"
    input_topic: str = "ta"
    trade_ingestion_mode: TradeIngestionMode = TradeIngestionMode.LIVE

    # feature group settings
    fg_name: str = "technical_analysis"
    fg_version: int = 1
    fg_pk: list[str] = ["symbol", "timeframe"]
    fg_event_time: str = "timestamp"

    # secrets
    hopsworks_api_key: str = "hopsworks_api_key"
    hopsworks_project_name: str = "hopsworks_project_name"


@lru_cache()
def features_settings() -> Settings:
    return Settings()
