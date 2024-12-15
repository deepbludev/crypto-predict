from llama_index.llms.ollama import Ollama

from domain.llm import LLMModel

from .analyzer import SentimentAnalyzer


class OllamaSentimentAnalyzer(SentimentAnalyzer):
    """Sentiment analyzer using Ollama."""

    def __init__(self, llm_model: LLMModel, base_url: str, temperature: float = 0):
        super().__init__(
            llm_model,
            llm=Ollama(
                model=llm_model,
                base_url=base_url,
                temperature=temperature,
            ),
        )
