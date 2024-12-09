from __future__ import annotations

from typing import Iterable, Self

import numpy as np
from talib import stream

from domain.candles import CandleProps
from domain.core import NDFloats, Schema


class RSI(Schema):
    """Relative Strength Index (RSI)"""

    rsi_9: float
    rsi_14: float
    rsi_21: float
    rsi_28: float

    @classmethod
    def calc_rsi(
        cls,
        close: NDFloats,
    ) -> RSI:
        """
        Calculate the Relative Strength Index (RSI) for a given period in days.

        Args:
            close_values: The closing prices of the asset
            period: The period in days to calculate the RSI
        Returns:
            The calculated RSI
        """
        return RSI(
            rsi_9=stream.RSI(close, timeperiod=9),
            rsi_14=stream.RSI(close, timeperiod=14),
            rsi_21=stream.RSI(close, timeperiod=21),
            rsi_28=stream.RSI(close, timeperiod=28),
        )


class TechnicalAnalysis(
    CandleProps,
    RSI,
):
    """Technical analysis of a candle."""

    @classmethod
    def calc(
        cls,
        candle: CandleProps,
        high_values: Iterable[float],
        low_values: Iterable[float],
        close_values: Iterable[float],
        volume_values: Iterable[float],
    ) -> Self:
        _high, _low, close, _volume = [
            np.array(list(v))
            for v in [
                high_values,
                low_values,
                close_values,
                volume_values,
            ]
        ]

        return cls(
            **candle.unpack(),
            **RSI.calc_rsi(close).unpack(),
        )
