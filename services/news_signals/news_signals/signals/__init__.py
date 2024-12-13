from domain.llm import LLMProvider
from news_signals.core.settings import news_signals_settings

from .analyzer import SentimentAnalyzer
from .anthropic import AnthropicSentimentAnalyzer
from .ollama import OllamaSentimentAnalyzer


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Gets the sentiment analyzer for the given provider."""
    settings = news_signals_settings()
    provider, model = settings.llm_provider, settings.llm_model

    match provider:
        case LLMProvider.OLLAMA:
            return OllamaSentimentAnalyzer(model)

        case LLMProvider.ANTHROPIC:
            return AnthropicSentimentAnalyzer(model)
