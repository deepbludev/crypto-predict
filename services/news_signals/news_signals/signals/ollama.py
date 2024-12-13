from llama_index.llms.ollama import Ollama

from domain.llm import LLMModel
from domain.news import NewsStory
from domain.sentiment_analysis import (
    NewsStorySentimentAnalysis,
)

from .analyzer import SentimentAnalyzer


class OllamaSentimentAnalyzer(SentimentAnalyzer):
    """Sentiment analyzer using Ollama."""

    def __init__(self, llm_model: LLMModel):
        self.llm = Ollama(model=llm_model, temperature=0)
        super().__init__(llm_model)

    def analyze(self, story: NewsStory) -> NewsStorySentimentAnalysis:
        # TODO: Implement the sentiment analysis
        return NewsStorySentimentAnalysis(
            story=story.title,
            timestamp=story.timestamp,
            reasoning="Dummy reasoning",
            llm_model=self.llm_model,
        )
