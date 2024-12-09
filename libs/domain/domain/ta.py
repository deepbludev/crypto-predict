from __future__ import annotations

from typing import Iterable, Self

import numpy as np
from talib import stream

from domain.candles import CandleProps
from domain.core import NDFloats, Schema


class RSI(Schema):
    """
    Relative Strength Index (RSI).

    It includes the RSI at 9, 14, 21, 28 days.
    """

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
            The calculated RSI at 9, 14, 21, 28 days
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
            The calculated MACD at the given periods
        """
        macd, macd_signal, macd_hist = stream.MACD(
            close,
            fastperiod=fast_period,
            slowperiod=slow_period,
            signalperiod=signal_period,
        )
        return MACD(macd=macd, macd_signal=macd_signal, macd_hist=macd_hist)


class BBANDS(Schema):
    """
    Bollinger Bands (BBANDS).

    It includes the Bollinger Bands upper, middle and lower.
    The default periods are 20 days, stddev 2 and the moving average type is simple (0).
    """

    bbands_upper: float
    bbands_middle: float
    bbands_lower: float

    @staticmethod
    def calc_bbands(
        close: NDFloats,
        period: int = 20,
        nbdevup: int = 2,
        nbdevdn: int = 2,
        matype: int = 0,
    ) -> BBANDS:
        bbands_upper, bbands_middle, bbands_lower = stream.BBANDS(
            close,
            timeperiod=period,
            nbdevup=nbdevup,
            nbdevdn=nbdevdn,
            matype=matype,
        )
        return BBANDS(
            bbands_upper=bbands_upper,
            bbands_middle=bbands_middle,
            bbands_lower=bbands_lower,
        )


class STOCHRSI(Schema):
    """
    Stochastic Relative Strength Index (STOCHRSI).

    It includes the fastk and fastd. The defaults are
    14 days, 5 fastk period, 3 fastd period and fastd moving average type simple.
    """

    stochrsi_fastk: float
    stochrsi_fastd: float

    @staticmethod
    def calc_stochrsi(
        close: NDFloats,
        period: int = 14,
        fastk_period: int = 5,
        fastd_period: int = 3,
        fastd_matype: int = 0,
    ) -> STOCHRSI:
        stochrsi_fastk, stochrsi_fastd = stream.STOCHRSI(
            close,
            period,
            fastk_period,
            fastd_period,
            fastd_matype,
        )
        return STOCHRSI(stochrsi_fastk=stochrsi_fastk, stochrsi_fastd=stochrsi_fastd)


class TechnicalAnalysis(
    CandleProps,
    RSI,
    MACD,
    BBANDS,
    STOCHRSI,
):
    """Technical analysis of a candle.
    It includes the candle properties and the following technical indicators:

    - Relative Strength Index (RSI at 9, 14, 21, 28 days)
    - Moving Average Convergence Divergence (MACD at 12, 26, 9 days)
    - Bollinger Bands (BBANDS at 20 days, stddev 2, moving average type simple)
    - Stochastic Relative Strength Index (STOCHRSI at 10 days, 5 fastk period,
    3 fastd period, fastd moving average type simple)

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
            **cls.calc_bbands(close).unpack(),
            **cls.calc_stochrsi(close, period=10).unpack(),
        )
