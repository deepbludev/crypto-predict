from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from domain.candles import CandleTimeframe
from domain.core import DeploymentEnv
from domain.ta import TechnicalIndicator as TI
from domain.trades import Symbol


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/price_predictions/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="price_predictions_",
    )

    # broker settings
    broker_address: str = "localhost:19092"
    consumer_group: str = "cg_price_predictions"
    input_topic: str = "candles"

    # model training settings
    deployment_env: DeploymentEnv = DeploymentEnv.DEV
    days_back: int = 30
    symbol: Symbol = Symbol.BTCUSD
    timeframe: CandleTimeframe = CandleTimeframe.tf_1m
    target_horizon: int = 5
    hyperparam_tuning_search_trials: int = 0
    hyperparam_tuning_n_splits: int = 3
    ta_features: list[TI] = [
        TI.SMA_21,
        TI.RSI_21,
        TI.MACD,
        TI.MACD_SIGNAL,
        TI.MACD_HIST,
        TI.BBANDS_UPPER,
        TI.BBANDS_MIDDLE,
        TI.BBANDS_LOWER,
        TI.STOCHRSI_FASTK,
        TI.STOCHRSI_FASTD,
        TI.ADX,
        TI.VOLUME_EMA,
        TI.ICHIMOKU_CONV,
        TI.ICHIMOKU_BASE,
        TI.ICHIMOKU_SPAN_A,
        TI.ICHIMOKU_SPAN_B,
        TI.MFI,
        TI.ATR,
        TI.ROC,
    ]

    # feature view settings
    fview_name: str = "price_predictions"
    fview_version: int = 1

    # feature groups settings
    ta_fgroup_name: str = "ta"
    ta_fgroup_version: int = 1
    news_signals_fgroup_name: str = "news_signals"
    news_signals_fgroup_version: int = 1

    # hopsworks credentials
    hopsworks_api_key: str = "hopsworks_api_key"
    hopsworks_project_name: str = "hopsworks_project_name"

    # comet ml credentials
    comet_ml_api_key: str = "comet_ml_api_key"
    comet_ml_workspace: str = "comet_ml_workspace"
    comet_ml_project: str = "comet_ml_project"

    # elasticsearch credentials
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "price_predictions"


@lru_cache()
def price_predictions_settings() -> Settings:
    return Settings()
