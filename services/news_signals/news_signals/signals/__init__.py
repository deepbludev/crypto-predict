from domain.llm import LLMProvider
from news_signals.core.settings import news_signals_settings

from .analyzer import SentimentAnalyzer
from .ollama import OllamaSentimentAnalyzer


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Gets the sentiment analyzer for the given provider."""
    settings = news_signals_settings()
    provider, model = settings.llm_provider, settings.llm_model

    match provider:
        case LLMProvider.OLLAMA:
            return OllamaSentimentAnalyzer(model)

        # Add more providers here...
        # case LLMProvider.ANTHROPIC:
        # ...
        case _:
            raise ValueError(f"Unknown provider: {provider}")
