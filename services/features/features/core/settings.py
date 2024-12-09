from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/features/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="features_",
    )

    broker_address: str = "localhost:19092"
    consumer_group: str = "cg_features"
    input_topic: str = "ta"
    fg_name: str = "technical_analysis"
    fg_version: str = "1"
    fg_pk: list[str] = ["symbol", "timeframe"]
    fg_event_time: str = "timestamp"

    # secrets
    hopsworks_api_key: str = "hopsworks_api_key"
    hopsworks_project_name: str = "hopsworks_project_name"


@lru_cache()
def features_settings() -> Settings:
    return Settings()
