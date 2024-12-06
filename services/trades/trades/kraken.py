"""
Kraken websocket API implementation using async websockets.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncIterator

import websockets
from loguru import logger
from pydantic import BaseModel, Field, ValidationError, field_serializer
from quixstreams import Application as QuixApp
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from domain.trades import Symbol, Trade


class KrakenTrade(BaseModel):
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
        return Trade.model_validate(self.model_dump(by_alias=True))

    @classmethod
    def to_kraken_symbol(cls, symbol: Symbol) -> str:
        """Adds a slash to the symbol to match the Kraken API format."""
        return f"{symbol[:3]}/{symbol[3:]}"


def is_trade(response: dict[str, Any]) -> bool:
    return response.get("channel") == "trade"


def is_heartbeat(response: dict[str, Any]) -> bool:
    return response.get("channel") == "heartbeat"


class KrakenWebsocketAPI:
    _url = "wss://ws.kraken.com/v2"

    def __init__(self, symbols: list[Symbol]):
        """
        Initializes the Kraken websocket API with the given symbols,
        converting them to the format expected by the Kraken API.
        """
        self.symbols = list(map(KrakenTrade.to_kraken_symbol, symbols))
        self.ws = None

    async def connect(self):
        """
        Establishes the websocket connection and subscribes to trades.
        """
        self.ws = await websockets.connect(self._url)
        ws = self.check_connection()

        subscribe_msg = {
            "method": "subscribe",
            "params": {
                "channel": "trade",
                "symbol": self.symbols,
                "snapshot": True,
            },
        }
        await ws.send(json.dumps(subscribe_msg))

    def check_connection(self):
        """
        Checks if the websocket connection is established,
        raising a RuntimeError if it is not.
        """
        if self.ws is None:
            raise RuntimeError("Websocket not connected. Call connect() first.")
        return self.ws

    async def stream_trades(self) -> AsyncIterator[Trade]:
        """
        Receives messages from the websocket and yields Trade objects.
        If the message is not a trade message or is malformed, it skips it.
        """
        ws = self.check_connection()
        while True:
            try:
                message = await ws.recv()
                response = json.loads(message)
                if not is_trade(response):
                    if is_heartbeat(response):
                        logger.info("Received heartbeat from Kraken")
                    else:
                        logger.info("Received non-trade message from Kraken")
                    continue

                trades = response.get("data", [])
                for trade in trades:
                    try:
                        yield KrakenTrade.model_validate(trade).into()
                    except ValidationError as e:
                        logger.error(f"Error validating trade from Kraken: {e}")

            except ConnectionClosedOK:
                # Normal closure
                logger.info("WebSocket connection closed normally.")
                break
            except ConnectionClosedError as e:
                # Abnormal closure
                logger.error(f"WebSocket connection closed with error: {e}")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue


async def process_kraken_trades(
    kraken: KrakenWebsocketAPI,
    messagebus: QuixApp,
    topic_name: str,
):
    """
    Background task that processes Krakentrades.
    It uses the Kraken websocket API to get the trades and the Quix messagebus
    to produce them.
    """
    topic = messagebus.topic(name=topic_name, value_serializer="json")
    try:
        with messagebus.get_producer() as producer:
            async for trade in kraken.stream_trades():
                message = topic.serialize(
                    key=trade.symbol,
                    value=trade.serialize(),
                )
                producer.produce(topic=topic.name, value=message.value, key=message.key)
                logger.info(f"Produced trade (Kraken): {trade.symbol} {trade.price}")

    except asyncio.CancelledError:
        logger.info("Trade processing task from Kraken was cancelled")
        raise
    except Exception as e:
        logger.error(f"Error processing trades: {e}")
    finally:
        logger.info("Trade processing task has terminated")
