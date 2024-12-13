from abc import ABC, abstractmethod

from domain.news import NewsStory
from domain.sentiment_analysis import SentimentAnalysisResult


class SentimentAnalyzer(ABC):
    @abstractmethod
    def analyze(self, story: NewsStory) -> SentimentAnalysisResult:
        """Analyze the sentiment of the given news story."""
        ...
