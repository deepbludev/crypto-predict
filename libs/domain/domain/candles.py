from __future__ import annotations

from enum import Enum
from typing import Self

from domain.core import Schema
from domain.trades import Exchange, Symbol, Trade


class CandleTimeframe(str, Enum):
    """The timeframe of a candle."""

    tf_1m = "1m"
    tf_5m = "5m"
    tf_15m = "15m"
    tf_30m = "30m"
    tf_1h = "1h"
    tf_4h = "4h"
    tf_1D = "1D"
    tf_1W = "1W"
    tf_1M = "1M"

    def to_sec(self) -> int:
        """Convert the timeframe to seconds."""
        match self:
            case CandleTimeframe.tf_1m:
                return 60 * 1
            case CandleTimeframe.tf_5m:
                return 60 * 5
            case CandleTimeframe.tf_15m:
                return 60 * 15
            case CandleTimeframe.tf_30m:
                return 60 * 30
            case CandleTimeframe.tf_1h:
                return 60 * 60 * 1
            case CandleTimeframe.tf_4h:
                return 60 * 60 * 4
            case CandleTimeframe.tf_1D:
                return 60 * 60 * 24
            case CandleTimeframe.tf_1W:
                return 60 * 60 * 24 * 7
            case CandleTimeframe.tf_1M:
                return 60 * 60 * 24 * 30


class EmissionMode(str, Enum):
    """The mode of emission of candles.

    LIVE: emit partial candles as soon as a new trade is received
    FULL: emit full candles only after the window is closed
    """

    LIVE = "LIVE"
    FULL = "FULL"


class CandleProps(Schema):
    """Properties of an OHLC candle."""

    symbol: Symbol
    timeframe: CandleTimeframe
    exchange: Exchange
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: int
    start: int | None = None
    end: int | None = None


class Candle(CandleProps):
    """
    Represents an OHLC candle.

    Attributes:
        symbol: The symbol of the candle.
        timeframe: The window size of the candle.
        open: The open price of the candle.
        high: The highest price of the candle.
        low: The lowest price of the candle.
        close: The close price of the candle.
        volume: The volume of the candle.
        timestamp: The timestamp of the candle in milliseconds.
        start: The start timestamp of the candle window in milliseconds.
        end: The end timestamp of the candle window in milliseconds.
    """

    @classmethod
    def init(cls, timeframe: CandleTimeframe, first_trade: Trade) -> Self:
        """
        Initialize a candle from a trade, using the first trade as the open price.

        Args:
            timeframe: The window size of the candle.
            first_trade: The trade to initialize the candle with.

        Returns:
            A newly initialized candle.
        """
        return cls(
            symbol=first_trade.symbol,
            timeframe=timeframe,
            exchange=first_trade.exchange,
            open=first_trade.price,
            high=first_trade.price,
            low=first_trade.price,
            close=first_trade.price,
            volume=first_trade.volume,
            timestamp=first_trade.timestamp,
        )

    def close_window(self, start: int, end: int) -> Self:
        """Close the candle with the given start and end timestamps."""
        self.start = start
        self.end = end
        return self

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

    def is_compatible(self, other: Candle | None) -> bool:
        """
        Check if the candle is compatible with the other given candle.
        Candles must have the same symbol and timeframe in order to be considered
        compatible.
        """
        if not other:
            return False

        return self.symbol == other.symbol and self.timeframe == other.timeframe

    def is_same_window(self, other: Candle | None) -> bool:
        """
        Check if the candle is in the same window as the other given candle.
        Candles must be compatible and have the same start and end timestamps.
        """
        if not other:
            return False

        return (
            self.is_compatible(other)
            and self.start == other.start
            and self.end == other.end
        )
