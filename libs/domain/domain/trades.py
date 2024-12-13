from enum import Enum

from domain.core import Schema


class TradeIngestionMode(str, Enum):
    """
    The mode of ingestion of trades.

    LIVE: ingest trades from a live source
    HISTORICAL: ingest trades from a historical source
    """

    LIVE = "LIVE"
    HISTORICAL = "HISTORICAL"

    def to_auto_reset_offset_mode(self):
        """Convert the ingestion mode to the auto-reset offset mode, used by kafka."""
        match self:
            case TradeIngestionMode.LIVE:
                return "earliest"
            case TradeIngestionMode.HISTORICAL:
                return "latest"


class Exchange(str, Enum):
    """Exchange Enum"""

    KRAKEN = "KRAKEN"
    BINANCE = "BINANCE"
    BYBIT = "BYBIT"
    BITMEX = "BITMEX"
    BITFINEX = "BITFINEX"
    BITGET = "BITGET"
    BITSTAMP = "BITSTAMP"
    BITTREX = "BITTREX"
    COINBASE = "COINBASE"
    GEMINI = "GEMINI"


class Asset(str, Enum):
    """Asset Enum"""

    BTC = "BTC"
    ETH = "ETH"
    XRP = "XRP"


class Symbol(str, Enum):
    """Trade symbols Enum"""

    # Crypto / USD
    XRPUSD = "XRPUSD"
    XLMUSD = "XLMUSD"
    BTCUSD = "BTCUSD"
    ETHUSD = "ETHUSD"
    # Crypto / EUR
    BTCEUR = "BTCEUR"
    XRPEUR = "XRPEUR"
    XLMEUR = "XLMEUR"
    ETHEUR = "ETHEUR"


class Trade(Schema):
    """
    Represents a trade from a crypto exchange.

    Attributes:
        symbol: The symbol of the trade (e.g. XRPUSD).
        price: The price of the trade based on the symbol (e.g. 0.5).
        volume: The volume of the trade based on the symbol (e.g. 100).
        timestamp: The timestamp of the trade in milliseconds.
    """

    symbol: Symbol
    price: float
    volume: float
    timestamp: int
    exchange: Exchange
