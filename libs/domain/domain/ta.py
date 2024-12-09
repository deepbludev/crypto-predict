from __future__ import annotations

from typing import Any, Iterable, Self

import numpy as np
from numpy.typing import NDArray
from talib import stream

from domain.candles import CandleProps
from domain.core import Schema

type NDFloats = NDArray[np.floating[Any]]
"""Type alias for a numpy array of floats."""


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


class BollingerBands(Schema):
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
    ) -> BollingerBands:
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
        return BollingerBands(
            bbands_upper=bbands_upper,
            bbands_middle=bbands_middle,
            bbands_lower=bbands_lower,
        )


class StochasticRSI(Schema):
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
    ) -> StochasticRSI:
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
        return StochasticRSI(
            stochrsi_fastk=stochrsi_fastk, stochrsi_fastd=stochrsi_fastd
        )


class VolumeProfile(Schema):
    """
    Volume profile of the candle.
    Includes the volume EMA.
    """

    volume_ema: float

    @staticmethod
    def calc_volume_ema(volume: NDFloats, period: int = 10) -> VolumeProfile:
        """
        Calculate the Exponential Moving Average (EMA) of the volume.

        Args:
            volume: The volume of the asset
            period: The period to calculate the EMA (default 10)
        Returns:
            The calculated EMA of the volume
        """
        volume_ema = stream.EMA(volume, timeperiod=period)
        return VolumeProfile(volume_ema=volume_ema)


class AvgDirectionalIndex(Schema):
    """
    Average Directional Index (ADX).
    Includes the adx at the given period.
    """

    adx: float

    @staticmethod
    def calc_adx(
        high: NDFloats,
        low: NDFloats,
        close: NDFloats,
        period: int = 14,
    ) -> AvgDirectionalIndex:
        """
        Calculate the Average Directional Index (ADX) for the given period.

        Args:
            high: The high prices of the asset
            low: The low prices of the asset
            close: The closing prices of the asset
            period: The period to calculate the ADX (default 14)
        Returns:
            The calculated ADX at the given period
        """
        adx = stream.ADX(high, low, close, timeperiod=period)
        return AvgDirectionalIndex(adx=adx)


class IchimokuCloud(Schema):
    """
    Ichimoku Cloud (Ichimoku).
    Includes the Ichimoku conversion, base, leading span A and leading span B.
    """

    ichimoku_conv: float
    ichimoku_base: float
    ichimoku_span_a: float
    ichimoku_span_b: float

    @staticmethod
    def calc_ichimoku(
        close: NDFloats,
        conv_period: int = 9,
        base_period: int = 20,
        span_period: int = 40,
    ) -> IchimokuCloud:
        """
        Calculate the Ichimoku Cloud (Ichimoku) for the given periods.

        Args:
            close: The closing prices of the asset
            conv_period: The period for the Ichimoku conversion (default 9)
            base_period: The period for the Ichimoku base (default 20)
            span_period: The period for the Ichimoku span (default 40)
        Returns:
            The calculated Ichimoku Cloud at the given periods
        """
        return IchimokuCloud(
            ichimoku_conv=(conv := stream.EMA(close, timeperiod=conv_period)),
            ichimoku_base=(base := stream.EMA(close, timeperiod=base_period)),
            ichimoku_span_a=(conv + base) / 2,
            ichimoku_span_b=stream.EMA(close, timeperiod=span_period),
        )


class MoneyFlowIndex(Schema):
    """
    Money Flow Index (MFI).
    Includes the mfi at the given period.
    """

    mfi: float

    @staticmethod
    def calc_mfi(
        high: NDFloats,
        low: NDFloats,
        close: NDFloats,
        volume: NDFloats,
        period: int = 14,
    ) -> MoneyFlowIndex:
        """
        Calculate the Money Flow Index (MFI) for the given period.

        Args:
            high: The high prices of the asset
            low: The low prices of the asset
            close: The closing prices of the asset
            volume: The volume of the asset
            period: The period to calculate the MFI (default 14)
        Returns:
            The calculated MFI at the given period
        """
        mfi = stream.MFI(high, low, close, volume, timeperiod=period)
        return MoneyFlowIndex(mfi=mfi)


class AvgTrueRange(Schema):
    """
    Average True Range (ATR).
    Includes the atr at the given period.
    """

    atr: float

    @staticmethod
    def calc_atr(
        high: NDFloats,
        low: NDFloats,
        close: NDFloats,
        period: int = 10,
    ) -> AvgTrueRange:
        """
        Calculate the Average True Range (ATR) for the given period.

        Args:
            high: The high prices of the asset
            low: The low prices of the asset
            close: The closing prices of the asset
            period: The period to calculate the ATR (default 10)
        Returns:
            The calculated ATR at the given period
        """
        atr = stream.ATR(high, low, close, timeperiod=period)
        return AvgTrueRange(atr=atr)


class PriceROC(Schema):
    """
    Price Rate of Change (ROC).
    Includes the roc at the given period.
    """

    roc: float

    @staticmethod
    def calc_roc(close: NDFloats, period: int = 6) -> PriceROC:
        """
        Calculate the Price Rate of Change (ROC) for the given period.

        Args:
            close: The closing prices of the asset
            period: The period to calculate the ROC (default 6)
        Returns:
            The calculated ROC at the given period
        """
        roc = stream.ROC(close, timeperiod=period)
        return PriceROC(roc=roc)


class SMA(Schema):
    """
    Simple Moving Average (SMA).
    Includes the sma at 7, 14, 21, 28 days.
    """

    sma_7: float
    sma_14: float
    sma_21: float
    sma_28: float

    @staticmethod
    def calc_sma(close: NDFloats) -> SMA:
        """
        Calculate the Simple Moving Average (SMA) for 7, 14, 21, 28 days.

        Args:
            close: The closing prices of the asset
        Returns:
            The calculated SMA at 7, 14, 21, 28 days
        """
        return SMA(
            sma_7=stream.SMA(close, timeperiod=7),
            sma_14=stream.SMA(close, timeperiod=14),
            sma_21=stream.SMA(close, timeperiod=21),
            sma_28=stream.SMA(close, timeperiod=28),
        )


class TechnicalAnalysis(
    CandleProps,
    RSI,
    MACD,
    BollingerBands,
    StochasticRSI,
    AvgDirectionalIndex,
    VolumeProfile,
    IchimokuCloud,
    MoneyFlowIndex,
    AvgTrueRange,
    PriceROC,
    SMA,
):
    """Technical analysis of a candle.
    It includes the candle properties and the following technical indicators:

    - Relative Strength Index (RSI at 9, 14, 21, 28 days)
    - Moving Average Convergence Divergence (MACD at 12, 26, 9 days)
    - Bollinger Bands (BBANDS at 20 days, stddev 2, moving average type simple)
    - Stochastic Relative Strength Index (STOCHRSI at 10 days, 5 fastk period,
    3 fastd period, fastd moving average type simple)
    - Average Directional Index (ADX at 14 days)
    - Exponential Moving Average (EMA at 10 days)
    - Ichimoku Cloud (Ichimoku at 9, 20, 40 days)
    - Money Flow Index (MFI at 14 days)
    - Average True Range (ATR at 10 days)
    - Price Rate of Change (ROC at 6 days)
    - Simple Moving Average (SMA at 7, 14, 21, 28 days)
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
        high, low, close, volume = [
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
            **cls.calc_volume_ema(volume).unpack(),
            **cls.calc_ichimoku(close).unpack(),
            **cls.calc_mfi(high, low, close, volume).unpack(),
            **cls.calc_atr(high, low, close).unpack(),
            **cls.calc_roc(close).unpack(),
            **cls.calc_sma(close).unpack(),
        )