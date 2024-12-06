from typing import NewType

from pydantic import BaseModel

Symbol = NewType("Symbol", str)
"""
A type alias for a trade symbol.
"""


class Trade(BaseModel):
    """
    Represents a trade from a crypto exchange.
    """

    symbol: Symbol
    price: float
    volume: float
    timestamp: int = 0

    def serialize(self):
        return self.model_dump()
