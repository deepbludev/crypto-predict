from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/news/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="news_",
    )

    # broker settings
    broker_address: str = "localhost:19092"
    consumer_group: str = "cg_news"
    news_topic: str = "news"


@lru_cache()
def news_settings() -> Settings:
    return Settings()
