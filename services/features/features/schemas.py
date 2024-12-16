from __future__ import annotations

from domain.core import Schema
from domain.sentiment_analysis import AssetSentimentAnalysis


class Feature(Schema):
    """Base class for all features."""

    pass


class NewsStorySentimentAnalysisFeature(Feature, AssetSentimentAnalysis):
    """
    Feature for news story sentiment analysis.
    It represents the sentiment of the news story for a given asset,
    encoded as an integer.
    """

    sentiment: int  # type: ignore[reportIncompatibleVariableOverride]

    @classmethod
    def encode(cls, analysis: AssetSentimentAnalysis):
        """
        Encode the sentiment analysis domain object into a feature.
        """
        return cls(
            **analysis.unpack(),
            sentiment=analysis.sentiment.to_int(),
        )
