from domain.news import NewsStory
from domain.sentiment_analysis import (
    NewsStorySentimentAnalysis,
)

from .analyzer import SentimentAnalyzer


class OllamaSentimentAnalyzer(SentimentAnalyzer):
    def analyze(self, story: NewsStory) -> NewsStorySentimentAnalysis:
        # TODO: Implement the sentiment analysis
        return NewsStorySentimentAnalysis(
            story=story.title,
            timestamp=story.timestamp,
            reasoning="Dummy reasoning",
        )
