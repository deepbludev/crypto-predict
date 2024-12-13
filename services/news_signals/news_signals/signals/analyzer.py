from abc import ABC, abstractmethod

from domain.llm import LLMModel
from domain.news import NewsStory
from domain.sentiment_analysis import SentimentAnalysisResult


class SentimentAnalyzer(ABC):
    def __init__(self, llm_model: LLMModel):
        self.llm_model = llm_model

    @abstractmethod
    def analyze(self, story: NewsStory) -> SentimentAnalysisResult:
        """Analyze the sentiment of the given news story."""
        ...
