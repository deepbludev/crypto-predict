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
            close: The closing prices of the asset
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
            close: The closing prices of the asset
            fast_period: The fast period (default 12)
            slow_period: The slow period (default 26)
            signal_period: The signal period (default 9)
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
        """
        Calculate the Bollinger Bands (BBANDS) for the given periods.

        Args:
            close: The closing prices of the asset
            period: The period to calculate the BBANDS (default 20)
            nbdevup: The stdev multiplier for the upper band (default 2)
            nbdevdn: The stdev multiplier for the lower band (default 2)
            matype: The moving average type (default 0)
        Returns:
            The calculated BBANDS at the given periods
        """
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
    It includes the fastk and fastd.
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
        """
        Calculate the Stochastic Relative Strength Index (STOCHRSI)
        for the given periods.

        Args:
            close: The closing prices of the asset
            period: The period for the STOCHRSI (default 14)
            fastk_period: The fastk period (default 5)
            fastd_period: The fastd period (default 3)
            fastd_matype: The fastd moving average type (default 0)
        Returns:
            The calculated STOCHRSI at the given periods
        """
        stochrsi_fastk, stochrsi_fastd = stream.STOCHRSI(
            close,
            period,
            fastk_period,
            fastd_period,
            fastd_matype,
        )
        return STOCHRSI(stochrsi_fastk=stochrsi_fastk, stochrsi_fastd=stochrsi_fastd)


class ADX(Schema):
    """
    Average Directional Index (ADX).
    The default period is 14 days.
    """

    adx: float

    @staticmethod
    def calc_adx(
        high: NDFloats, low: NDFloats, close: NDFloats, period: int = 14
    ) -> ADX:
        adx = stream.ADX(high, low, close, timeperiod=period)
        return ADX(adx=adx)


class TechnicalAnalysis(
    CandleProps,
    RSI,
    MACD,
    BBANDS,
    STOCHRSI,
    ADX,
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
        """
        Calculate the technical analysis of a candle.

        Args:
            candle: The candle to calculate the technical analysis
            high_values: The high prices of the candle
            low_values: The low prices of the candle
            close_values: The closing prices of the candle
            volume_values: The volume of the candle
        Returns:
            The technical analysis of the candle
        """

        # convert the values to numpy arrays
        high, low, close, _volume = [
            np.array(list(v))
            for v in [high_values, low_values, close_values, volume_values]
        ]

        return cls(
            **candle.unpack(),
            **cls.calc_rsi(close).unpack(),
            **cls.calc_macd(close).unpack(),
            **cls.calc_bbands(close).unpack(),
            **cls.calc_stochrsi(close, period=10).unpack(),
            **cls.calc_adx(high, low, close).unpack(),
        )
