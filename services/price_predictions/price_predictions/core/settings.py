from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from domain.candles import CandleTimeframe
from domain.llm import LLMName
from domain.trades import Asset


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/price_predictions/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="price_predictions_",
    )

    asset: Asset = Asset.BTC
    timeframe: CandleTimeframe = CandleTimeframe.tf_1h
    llm_name: LLMName = LLMName.LLAMA_3_2_3B

    # feature view settings
    fview_name: str = "price_predictions"
    fview_version: int = 1

    # feature groups settings
    ta_fgroup_name: str = "ta"
    ta_fgroup_version: int = 1
    news_signals_fgroup_name: str = "news_signals"
    news_signals_fgroup_version: int = 1

    # secrets
    hopsworks_api_key: str = "hopsworks_api_key"
    hopsworks_project_name: str = "hopsworks_project_name"


@lru_cache()
def price_predictions_settings() -> Settings:
    return Settings()
