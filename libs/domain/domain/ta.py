from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, Self

import numpy as np
from numpy.typing import NDArray
from pydantic import computed_field
from talib import stream

from domain.candles import CandleProps
from domain.core import Schema
from domain.trades import Asset

type NDFloats = NDArray[np.floating[Any]]
"""Type alias for a numpy array of floats."""


class TechnicalIndicator(str, Enum):
    """Technical indicator names"""

    RSI_9 = "rsi_9"
    RSI_14 = "rsi_14"
    RSI_21 = "rsi_21"
    RSI_28 = "rsi_28"
    MACD = "macd"
    MACD_SIGNAL = "macd_signal"
    MACD_HIST = "macd_hist"
    BBANDS_UPPER = "bbands_upper"
    BBANDS_MIDDLE = "bbands_middle"
    BBANDS_LOWER = "bbands_lower"
    STOCHRSI_FASTK = "stochrsi_fastk"
    STOCHRSI_FASTD = "stochrsi_fastd"
    ADX = "adx"
    VOLUME_EMA = "volume_ema"
    ICHIMOKU_CONV = "ichimoku_conv"
    ICHIMOKU_BASE = "ichimoku_base"
    ICHIMOKU_SPAN_A = "ichimoku_span_a"
    ICHIMOKU_SPAN_B = "ichimoku_span_b"
    MFI = "mfi"
    ATR = "atr"
    PRICE_ROC = "price_roc"
    SMA_7 = "sma_7"
    SMA_14 = "sma_14"
    SMA_21 = "sma_21"
    SMA_28 = "sma_28"


class RSI(Schema):
    """
    Relative Strength Index (RSI).
    It includes the RSI at 9, 14, 21, 28.
    """

    rsi_9: float | None
    rsi_14: float | None
    rsi_21: float | None
    rsi_28: float | None

    @staticmethod
    def calc_rsi(close: Iterable[float]) -> RSI:
        """
        Calculate the Relative Strength Index (RSI) for the periods 9, 14, 21, 28

        Args:
            close: The closing prices of the asset
        Returns:
            The calculated RSI at 9, 14, 21, 28
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

    macd: float | None
    macd_signal: float | None
    macd_hist: float | None

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

    bbands_upper: float | None
    bbands_middle: float | None
    bbands_lower: float | None

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

    stochrsi_fastk: float | None
    stochrsi_fastd: float | None

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

    volume_ema: float | None

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

    adx: float | None

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

    ichimoku_conv: float | None
    ichimoku_base: float | None
    ichimoku_span_a: float | None
    ichimoku_span_b: float | None

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

    mfi: float | None

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

    atr: float | None

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

    roc: float | None

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
    Includes the sma at 7, 14, 21, 28.
    """

    sma_7: float | None
    sma_14: float | None
    sma_21: float | None
    sma_28: float | None

    @staticmethod
    def calc_sma(close: NDFloats) -> SMA:
        """
        Calculate the Simple Moving Average (SMA) for 7, 14, 21, 28.

        Args:
            close: The closing prices of the asset
        Returns:
            The calculated SMA at 7, 14, 21, 28
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

    - Relative Strength Index (RSI at 9, 14, 21, 28)
    - Moving Average Convergence Divergence (MACD at 12, 26, 9)
    - Bollinger Bands (BBANDS at 20, stddev 2, moving average type simple)
    - Stochastic Relative Strength Index (STOCHRSI at 10, 5 fastk period,
    3 fastd period, fastd moving average type simple)
    - Average Directional Index (ADX at 14)
    - Exponential Moving Average (EMA at 10)
    - Ichimoku Cloud (Ichimoku at 9, 20, 40)
    - Money Flow Index (MFI at 14)
    - Average True Range (ATR at 10)
    - Price Rate of Change (ROC at 6)
    - Simple Moving Average (SMA at 7, 14, 21, 28)
    """

    @computed_field
    @property
    def asset(self) -> Asset:
        """The asset of the candle."""
        return self.symbol.to_asset()

    def key(self):
        return f"{self.symbol.value}-{self.timeframe.value}-{self.timestamp}"

    @classmethod
    def calc(
        cls,
        candle: CandleProps,
        high: Iterable[float],
        low: Iterable[float],
        close: Iterable[float],
        volume: Iterable[float],
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
        high_, low_, close_, volume_ = [
            np.array(list(v)) for v in [high, low, close, volume]
        ]

        return cls(
            **candle.unpack(),
            **cls.calc_rsi(close_).unpack(),
            **cls.calc_macd(close_).unpack(),
            **cls.calc_bbands(close_).unpack(),
            **cls.calc_stochrsi(close_, period=10).unpack(),
            **cls.calc_adx(high_, low_, close_).unpack(),
            **cls.calc_volume_ema(volume_).unpack(),
            **cls.calc_ichimoku(close_).unpack(),
            **cls.calc_mfi(high_, low_, close_, volume_).unpack(),
            **cls.calc_atr(high_, low_, close_).unpack(),
            **cls.calc_roc(close_).unpack(),
            **cls.calc_sma(close_).unpack(),
        )
