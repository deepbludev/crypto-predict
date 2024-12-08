from __future__ import annotations

from enum import Enum
from typing import Self

from pydantic import BaseModel

from domain.trades import Symbol, Trade


class CandleWindowSize(str, Enum):
    """The window size of a candle."""

    CANDLE_1m = "1m"
    CANDLE_5m = "5m"
    CANDLE_15m = "15m"
    CANDLE_30m = "30m"
    CANDLE_1h = "1h"
    CANDLE_4h = "4h"
    CANDLE_1D = "1D"
    CANDLE_1W = "1W"
    CANDLE_1M = "1M"


class Candle(BaseModel):
    """
    Represents an OHLC candle.

    Attributes:
        symbol: The symbol of the candle.
        window_size: The window size of the candle.
        open: The open price of the candle.
        high: The highest price of the candle.
        low: The lowest price of the candle.
        close: The close price of the candle.
        volume: The volume of the candle.
        timestamp: The timestamp of the candle in milliseconds.
    """

    symbol: Symbol
    window_size: CandleWindowSize
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: int

    @classmethod
    def init(cls, window_size: CandleWindowSize, first_trade: Trade) -> Self:
        """
        Initialize a candle from a trade, using the first trade as the open price.

        Args:
            window_size: The window size of the candle.
            first_trade: The trade to initialize the candle with.

        Returns:
            A newly initialized candle.
        """
        return cls(
            symbol=first_trade.symbol,
            window_size=window_size,
            open=first_trade.price,
            high=first_trade.price,
            low=first_trade.price,
            close=first_trade.price,
            volume=first_trade.volume,
            timestamp=first_trade.timestamp,
        )

    def update(self, trade: Trade) -> Self:
        """
        Update the candle with a new trade.

        Args:
            trade: The trade to update the candle with.
        """
        self.high = max(self.high, trade.price)
        self.low = min(self.low, trade.price)
        self.close = trade.price
        self.volume += trade.volume
        self.timestamp = trade.timestamp

        return self
