from __future__ import annotations

from typing import Iterable, Self

import numpy as np
from talib import stream

from domain.candles import CandleProps
from domain.core import NDFloats

type RSI = float


class TechnicalAnalysis(CandleProps):
    """Technical analysis of a candle."""

    rsi_9: RSI
    rsi_14: RSI
    rsi_21: RSI
    rsi_28: RSI

    @classmethod
    def calc(
        cls,
        candle: CandleProps,
        high_values: Iterable[float],
        low_values: Iterable[float],
        close_values: Iterable[float],
    ) -> Self:
        _high, _low, close = [
            np.array(v) for v in [high_values, low_values, close_values]
        ]

        return cls(
            # Candle details
            **candle.unpack(),
            # RSI
            rsi_9=cls.rsi(close, period=9),
            rsi_14=cls.rsi(close, period=14),
            rsi_21=cls.rsi(close, period=21),
            rsi_28=cls.rsi(close, period=28),
        )

    @classmethod
    def rsi(cls, close_values: NDFloats, period: int) -> RSI:
        """Calculate the Relative Strength Index (RSI) for a given period in days."""
        return stream.RSI(close_values, timeperiod=period)
