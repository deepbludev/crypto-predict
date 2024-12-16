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

    def to_int(self) -> int:
        match self:
            case SentimentSignal.BULLISH:
                return 1
            case SentimentSignal.BEARISH:
                return -1


class AssetSentimentAnalysis(Schema):
    asset: Asset = Field(description="The asset to analyze the sentiment for")
    sentiment: SentimentSignal = Field(
        description=dedent("""
            The sentiment signal for the asset, based on the impact

            - BULLISH if the price is expected to go up
            - BEARISH if it is expected to go down
        """).strip(),  # noqa: E501
    )


class NewsStorySentimentAnalysis(Schema):
    story: str
    timestamp: int = Field(default_factory=now_timestamp)
    llm_model: LLMModel
    asset_sentiments: list[AssetSentimentAnalysis]

    def to_feature(self) -> list[dict[str, Any]]:
        # TODO: extract logic to separate schema
        return [
            {
                "asset": s.asset,
                "sentiment": s.sentiment.to_int(),
                "story": self.story,
                "timestamp": self.timestamp,
                "llm_model": self.llm_model,
            }
            for s in self.asset_sentiments
        ]
