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
    NEUTRAL = "NEUTRAL"

    def to_int(self) -> int:
        match self:
            case SentimentSignal.BULLISH:
                return 1
            case SentimentSignal.BEARISH:
                return -1
            case SentimentSignal.NEUTRAL:
                return 0

    @classmethod
    def field_for(cls, asset: Asset):
        return Field(
            description=dedent(f"""
                The sentiment signal for the {asset} asset, based on the impact
                of the news on the {asset} price.

                - BULLISH if the price is expected to go up
                - NEUTRAL if it is expected to stay the same or the news is not related to {asset}
                - BEARISH if it is expected to go down
                """).strip(),  # noqa: E501
        )


class SentimentAnalysisResult(Schema):
    btc: str = SentimentSignal.field_for(Asset.BTC)
    eth: str = SentimentSignal.field_for(Asset.ETH)
    xrp: str = SentimentSignal.field_for(Asset.XRP)

    reasoning: str = Field(
        description="The reasoning behind the sentiment signals for the assets."
    )


class NewsStorySentimentAnalysis(Schema):
    story: str
    timestamp: int = Field(default_factory=now_timestamp)
    llm_model: LLMModel

    btc: SentimentSignal
    eth: SentimentSignal
    xrp: SentimentSignal
    reasoning: str

    def to_feature(self) -> dict[str, Any]:
        return self.unpack() | {
            "btc": self.btc.to_int(),
            "eth": self.eth.to_int(),
            "xrp": self.xrp.to_int(),
        }
