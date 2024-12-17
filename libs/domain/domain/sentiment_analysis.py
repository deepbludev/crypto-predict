from enum import Enum
from textwrap import dedent

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
        return [
            AssetSentimentAnalysis(
                **sentiment.unpack(),
                llm_model=self.llm_model,
                story=self.story,
                timestamp=self.timestamp,
            )
            for sentiment in self.asset_sentiments
        ]
