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

    @staticmethod
    def calc_rsi(close: NDFloats) -> RSI:
        """
        Calculate the Relative Strength Index (RSI) for the periods 9, 14, 21, 28 days

        Args:
            close_values: The closing prices of the asset
        Returns:
            The calculated RSI
        """
        return RSI(
            rsi_9=stream.RSI(close, timeperiod=9),
            rsi_14=stream.RSI(close, timeperiod=14),
            rsi_21=stream.RSI(close, timeperiod=21),
            rsi_28=stream.RSI(close, timeperiod=28),
        )


class MACD(Schema):
    """
    Moving Average Convergence Divergence (MACD).
    It includes the MACD, MACD signal and MACD histogram.
    The default periods are fast 12, slow 26, signal 9 days.
    """

    macd: float
    macd_signal: float
    macd_hist: float

    @staticmethod
    def calc_macd(
        close: NDFloats,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> MACD:
        """
        Calculate the Moving Average Convergence Divergence (MACD) the given periods.

        Args:
            close_values: The closing prices of the asset
            fast_period: The fast period to calculate the MACD (default 12)
            slow_period: The slow period to calculate the MACD (default 26)
            signal_period: The signal period to calculate the MACD (default 9)
        Returns:
            The calculated MACD
        """
        macd, macd_signal, macd_hist = stream.MACD(
            close,
            fastperiod=fast_period,
            slowperiod=slow_period,
            signalperiod=signal_period,
        )
        return MACD(macd=macd, macd_signal=macd_signal, macd_hist=macd_hist)


class TechnicalAnalysis(
    CandleProps,
    RSI,
    MACD,
):
    """Technical analysis of a candle.
    It includes the candle properties and the following technical indicators:

    - Relative Strength Index (RSI at 9, 14, 21, 28 days)
    - Moving Average Convergence Divergence (MACD at 12, 26, 9 days)
    - Bollinger Bands (BBANDS at 20 days, stddev 2)

    """

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
            **cls.calc_rsi(close).unpack(),
            **cls.calc_macd(close).unpack(),
        )
