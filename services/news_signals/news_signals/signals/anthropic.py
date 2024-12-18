from llama_index.llms.anthropic import Anthropic

from domain.llm import LLMName

from .analyzer import SentimentAnalyzer


class AnthropicSentimentAnalyzer(SentimentAnalyzer):
    """Sentiment analyzer using Anthropic."""

    def __init__(self, llm_name: LLMName, api_key: str, temperature: float = 0):
        super().__init__(
            llm_name,
            llm=Anthropic(
                model=llm_name,
                api_key=api_key,
                temperature=temperature,
            ),
        )
