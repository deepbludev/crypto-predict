from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from domain.llm import LLMModel, LLMProvider


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/news_signals/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="news_signals_",
    )

    broker_address: str = "localhost:19092"
    consumer_group: str = "cg_news_signals"
    input_topic: str = "news"
    output_topic: str = "news_signals"

    # LLM
    llm_provider: LLMProvider = LLMProvider.OLLAMA
    llm_model: LLMModel = LLMModel.LLAMA_3_2_3B

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Anthropic
    anthropic_api_key: str = "<anthropic-api-key>"


@lru_cache()
def news_signals_settings() -> Settings:
    return Settings()
