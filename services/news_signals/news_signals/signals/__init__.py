from domain.llm import LLMProvider

from .analyzer import SentimentAnalyzer
from .ollama import OllamaSentimentAnalyzer


def get_analyzer_for_provider(provider: LLMProvider) -> SentimentAnalyzer:
    match provider:
        case LLMProvider.OLLAMA:
            return OllamaSentimentAnalyzer()
        case _:
            raise ValueError(f"Unknown provider: {provider}")
