from enum import Enum

from domain.core import Schema


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
