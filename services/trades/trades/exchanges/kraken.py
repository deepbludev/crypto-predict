"""
Kraken websocket API implementation using async websockets.
"""

import json
from datetime import datetime
from typing import Any, AsyncIterator

import websockets
from loguru import logger
from pydantic import Field, ValidationError, field_serializer
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from domain.core import Schema
from domain.trades import Exchange, Symbol, Trade

from .client import TradesWsClient


class KrakenTrade(Schema):
    """
    Represents a trade snapshot from the Kraken API for a given symbol.
    """

    symbol: str
    price: float
    qty: float = Field(serialization_alias="volume")
    timestamp: datetime

    @field_serializer("symbol")
    def remove_slash_from_symbol(self, symbol: str, _info: Any):
        return Symbol(symbol.replace("/", ""))

    @field_serializer("timestamp")
    def timestamp_to_millis(self, dt: datetime, _info: Any):
        return int(dt.timestamp() * 1000)

    def into(self) -> Trade:
        return Trade.parse(
            self.model_dump(by_alias=True) | {"exchange": Exchange.KRAKEN}
        )

    @classmethod
    def to_kraken_symbol(cls, symbol: Symbol) -> str:
        """Adds a slash to the symbol to match the Kraken API format."""
        return f"{symbol[:3]}/{symbol[3:]}"


def is_trade(response: dict[str, Any]) -> bool:
    return response.get("channel") == "trade"


def is_heartbeat(response: dict[str, Any]) -> bool:
    return response.get("channel") == "heartbeat"


class KrakenTradesWsClient(TradesWsClient):
    """
    Kraken Websocket TradesAPI v2 implementation using async websockets.
    """

    def __init__(self, symbols: list[Symbol], url: str):
        """
        Initializes the Kraken websocket API with the given symbols,
        converting them to the format expected by the Kraken API.
        """
        self.kraken_symbols = list(map(KrakenTrade.to_kraken_symbol, symbols))
        super().__init__(name=Exchange.KRAKEN.value, url=url, symbols=symbols)

    async def connect(self):
        """
        Establishes the websocket connection and subscribes to trades.
        """
        self.ws = await websockets.connect(self.url)
        ws = self.check_connection()

        subscribe_msg = {
            "method": "subscribe",
            "params": {
                "channel": "trade",
                "symbol": self.kraken_symbols,
                "snapshot": True,
            },
        }
        await ws.send(json.dumps(subscribe_msg))
        logger.info(
            f"Subscribed to {[s.value for s in self.symbols]} trades from Kraken"
        )
        return self

    async def stream_trades(self) -> AsyncIterator[Trade]:
        """
        Receives messages from the websocket and yields Trade objects.
        If the message is not a trade message or is malformed, it skips it.
        """
        ws = self.check_connection()
        while True:
            try:
                message = await ws.recv()
                res = json.loads(message)

                if not is_trade(res):
                    message_type = "Heartbeat" if is_heartbeat(res) else "Non-trade"
                    logger.info(f"[{self.name}] {message_type}")
                    continue

                trades = res.get("data", [])
                for trade in trades:
                    try:
                        yield KrakenTrade.parse(trade).into()
                    except ValidationError as e:
                        logger.error(f"[{self.name}] Error validating trade: {e}")

            except ConnectionClosedOK:
                # Normal closure
                logger.info(f"[{self.name}] WebSocket connection closed normally")
                break
            except ConnectionClosedError as e:
                # Abnormal closure
                logger.error(
                    f"[{self.name}] WebSocket connection closed with error: {e}"
                )
                break
            except Exception as e:
                logger.error(f"[{self.name}] Error processing message: {e}")
                continue
