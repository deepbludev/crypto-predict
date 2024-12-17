from enum import Enum
from textwrap import dedent
from typing import Any

from pydantic import Field

from domain.core import Schema, now_timestamp
from domain.llm import LLMModel
from domain.trades import Asset


class SentimentSignal(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"

    def encoded(self) -> int:
        match self:
            case SentimentSignal.BULLISH:
                return 1
            case SentimentSignal.BEARISH:
                return -1


assets = [a.value for a in Asset]


class AssetSentimentAnalysisDetails(Schema):
    asset: Asset = Field(
        description=f"The asset to analyze the sentiment for. "
        f"Must be one of the assets in the asset list: {assets}"
    )
    sentiment: SentimentSignal = Field(
        description=dedent("""
            The sentiment signal for the asset, based on the impact

            - BULLISH if the price is expected to go up
            - BEARISH if it is expected to go down
        """).strip(),  # noqa: E501
    )


class AssetSentimentAnalysis(AssetSentimentAnalysisDetails):
    llm_model: LLMModel
    story: str
    timestamp: int = Field(default_factory=now_timestamp)


class NewsStorySentimentAnalysis(Schema):
    story: str
    timestamp: int = Field(default_factory=now_timestamp)
    llm_model: LLMModel
    asset_sentiments: list[AssetSentimentAnalysisDetails]

    def unwind(self) -> list[AssetSentimentAnalysis]:
        """
        Unwinds the sentiment analysis into a list of individual
        AssetSentimentAnalysis for each asset.
        """
        return [
            AssetSentimentAnalysis(
                **sentiment.unpack(),
                llm_model=self.llm_model,
                story=self.story,
                timestamp=self.timestamp,
            )
            for sentiment in self.asset_sentiments
        ]

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
            **{a.asset.value: a.sentiment.encoded() for a in self.asset_sentiments},
        }
