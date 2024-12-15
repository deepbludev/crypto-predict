from llama_index.llms.anthropic import Anthropic

from domain.llm import LLMModel

from .analyzer import SentimentAnalyzer


class AnthropicSentimentAnalyzer(SentimentAnalyzer):
    """Sentiment analyzer using Anthropic."""

    def __init__(self, llm_model: LLMModel, api_key: str, temperature: float = 0):
        super().__init__(
            llm_model,
            llm=Anthropic(
                model=llm_model,
                api_key=api_key,
                temperature=temperature,
            ),
        )
