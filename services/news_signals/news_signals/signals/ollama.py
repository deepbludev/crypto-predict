from llama_index.llms.ollama import Ollama

from domain.llm import LLMName

from .analyzer import SentimentAnalyzer


class OllamaSentimentAnalyzer(SentimentAnalyzer):
    """Sentiment analyzer using Ollama."""

    def __init__(self, llm_name: LLMName, base_url: str, temperature: float = 0):
        super().__init__(
            llm_name,
            llm=Ollama(
                model=llm_name,
                base_url=base_url,
                temperature=temperature,
            ),
        )
