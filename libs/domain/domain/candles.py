from __future__ import annotations

from enum import Enum
from typing import Self

from domain.core import Schema
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

    def to_sec(self) -> int:
        """Convert the window size to seconds."""
        match self:
            case CandleWindowSize.CANDLE_1m:
                return 60 * 1
            case CandleWindowSize.CANDLE_5m:
                return 60 * 5
            case CandleWindowSize.CANDLE_15m:
                return 60 * 15
            case CandleWindowSize.CANDLE_30m:
                return 60 * 30
            case CandleWindowSize.CANDLE_1h:
                return 60 * 60 * 1
            case CandleWindowSize.CANDLE_4h:
                return 60 * 60 * 4
            case CandleWindowSize.CANDLE_1D:
                return 60 * 60 * 24
            case CandleWindowSize.CANDLE_1W:
                return 60 * 60 * 24 * 7
            case CandleWindowSize.CANDLE_1M:
                return 60 * 60 * 24 * 30


class CandleProps(Schema):
    """Properties of an OHLC candle."""

    symbol: Symbol
    window_size: CandleWindowSize
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
        window_size: The window size of the candle.
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

    def same_window(self, other: Candle | None) -> bool:
        """
        Check if the candle is in the same window as the other given candle.
        Candles must have the same symbol and window size in order to be considered
        in the same window.
        """
        if not other:
            return False

        return (
            self.symbol == other.symbol
            and self.window_size == other.window_size
            and self.start == other.start
            and self.end == other.end
        )
