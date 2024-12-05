from datetime import datetime
from typing import Self

from pydantic import BaseModel, model_validator


class Trade(BaseModel):
    """
    Represents a trade from a crypto exchange.
    """

    pair: str
    price: float
    volume: float
    timestamp: datetime
    timestamp_ms: int = 0

    @model_validator(mode='after')
    def set_timestamp_in_ms_from_iso_datetime(self) -> Self:
        self.timestamp_ms = int(self.timestamp.timestamp() * 1000)
        return self

    def serialize(self) -> str:
        return self.model_dump_json()
