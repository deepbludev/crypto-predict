from enum import Enum
from textwrap import dedent
from typing import Any

from pydantic import Field, model_validator

from domain.core import Schema, now_timestamp
from domain.llm import LLMModel


class SentimentSignal(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"

    def encoded(self) -> int:
        match self:
            case SentimentSignal.BULLISH:
                return 1
            case SentimentSignal.BEARISH:
                return -1

    @classmethod
    def values(cls) -> list[str]:
        return [s.value for s in cls]


class AssetSentimentAnalysisDetails(Schema):
    """
    Represents the sentiment analysis for a single asset.
    """

    asset: str = Field(
        description=f"The asset to analyze the sentiment for. "
        f"Must be one of the assets in the asset list: {SentimentSignal.values()}"
    )
    sentiment: str = Field(
        description=dedent("""
            The sentiment signal for the asset, based on the impact

            - BULLISH if the price is expected to go up
            - BEARISH if it is expected to go down
        """).strip(),  # noqa: E501
    )

    def encoded(self) -> dict[str, Any]:
        return {
            "asset": self.asset,
            "sentiment": SentimentSignal(self.sentiment).encoded(),
        }


class NewsStorySentimentAnalysis(Schema):
    story: str
    timestamp: int = Field(default_factory=now_timestamp)
    llm_model: LLMModel
    asset_sentiments: list[AssetSentimentAnalysisDetails]

    @model_validator(mode="before")
    @classmethod
    def validate_sentiments_and_remove_invalid(
        cls, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validates the sentiments and removes invalid ones.
        """
        asset_sentiments = data.get("asset_sentiments", [])
        data["asset_sentiments"] = [
            a for a in asset_sentiments if a.sentiment in SentimentSignal
        ]
        return data

    def encoded(self) -> dict[str, Any]:
        """
        Encodes the sentiment analysis into a feature vector format
        that can be used for training a model.

        Returns:
            A dictionary with the following keys:
            - story: the news story
            - timestamp: the timestamp of the news story
            - llm_model: the LLM model used to analyze the news story
            - asset_sentiments: an unpacked list of AssetSentimentAnalysisDetails,
            with the asset as the key and the sentiment as the value.

            The sentiment is encoded as 1 for BULLISH and -1 for BEARISH.
            Example:
            ```python
            {
                "story": "SEC approves Bitcoin ETF. ETH loses credibility.",
                "timestamp": 1718534400,
                "llm_model": "llama3.2-3b",
                "BTC": 1,
                "ETH": -1,
            }
            ```
        """
        return {
            "story": self.story,
            "timestamp": self.timestamp,
            "llm_model": self.llm_model.value,
            **{
                a.asset: SentimentSignal(a.sentiment).encoded()
                for a in self.asset_sentiments
            },
        }
