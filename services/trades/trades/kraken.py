import json
from datetime import datetime
from typing import Any, Iterable

import websocket as ws
from loguru import logger
from pydantic import BaseModel, Field, ValidationError
from trades.trade import Trade


class KrakenTrade(BaseModel):
    """
    Represents a trade from the Kraken API. It is a snapshot of the trades
    for a given symbol and it is designed to easily convert to a generic Trade object.
    """

    symbol: str = Field(serialization_alias="pair")
    price: float
    qty: float = Field(serialization_alias="volume")
    timestamp: datetime

    def into(self) -> Trade:
        return Trade.model_validate(self.model_dump(by_alias=True))


def is_trade(response: dict[str, Any]) -> bool:
    return response.get("channel") == "trade"


class KrakenWebsocketAPI:
    _url = "wss://ws.kraken.com/v2"

    def __init__(self, symbols: list[str]):
        self.symbols = symbols
        self._client = ws.create_connection(self._url)
        self._subscribe()

    def get_trades(self) -> Iterable[Trade]:
        """
        Receives a raw string from the websocket and converts it into a list of Trade objects.
        If the message is not a trade message (such as a heartbeat), or the message is malformed,
        it returns an empty list.
        """
        try:
            response = json.loads(self._client.recv())
            if not is_trade(response):
                return []

            data = response.get("data", [])
            return (KrakenTrade.model_validate(trade).into() for trade in data)

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return []

        except ValidationError as e:
            logger.error(f"Error validating trade: {e}")
            return []

    def _subscribe(self):
        """
        Subscribes to the websocket and waits for the initial snapshot.
        """
        # send a subscribe message to the websocket
        subscribe_msg = dict(
            method="subscribe",
            params=dict(channel="trade", symbol=self.symbols, snapshot=True),
        )
        self._client.send(json.dumps(subscribe_msg))
