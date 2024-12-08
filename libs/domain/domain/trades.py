from enum import Enum

from pydantic import BaseModel


class Symbol(str, Enum):
    """Trade symbols Enum"""

    XRPUSD = "XRPUSD"
    XLMUSD = "XLMUSD"
    BTCUSD = "BTCUSD"
    ETHUSD = "ETHUSD"


class Trade(BaseModel):
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
    timestamp: int = 0

    def serialize(self):
        """Serialize the trade to a dictionary."""
        return self.model_dump()
