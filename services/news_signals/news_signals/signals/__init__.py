from loguru import logger

from domain.llm import LLMProvider
from news_signals.core.settings import news_signals_settings

from .analyzer import SentimentAnalyzer
from .anthropic import AnthropicSentimentAnalyzer
from .ollama import OllamaSentimentAnalyzer


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Gets the sentiment analyzer for the given provider."""
    settings = news_signals_settings()
    provider, model = settings.llm_provider, settings.llm_name

    match provider:
        case LLMProvider.OLLAMA:
            logger.info(
                f"Using Ollama: model={model.value}, base_url={settings.ollama_base_url}"  # noqa
            )
            return OllamaSentimentAnalyzer(
                model,
                base_url=settings.ollama_base_url,
            )

        case LLMProvider.ANTHROPIC:
            logger.info(f"Using Anthropic: model={model.value}")
            return AnthropicSentimentAnalyzer(
                model,
                api_key=settings.anthropic_api_key,
            )
