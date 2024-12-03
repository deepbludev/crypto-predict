"""
Kraken websocket API implementation using async websockets.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncIterator

import websockets
from loguru import logger
from pydantic import BaseModel, Field, ValidationError
from quixstreams import Application as QuixApp
from trades.trade import Trade
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK


class KrakenTrade(BaseModel):
    """
    Represents a trade snapshot from the Kraken API for a given symbol.
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
        self.ws = None

    async def connect(self):
        """
        Establishes the websocket connection and subscribes to trades.
        """
        self.ws = await websockets.connect(self._url)
        await self._subscribe()

    async def _subscribe(self):
        """
        Subscribes to the websocket and waits for the initial snapshot.
        """
        subscribe_msg = dict(
            method="subscribe",
            params=dict(channel="trade", symbol=self.symbols, snapshot=True),
        )
        if not self.ws:
            raise RuntimeError("Websocket not connected. Call connect() first.")

        await self.ws.send(json.dumps(subscribe_msg))

    async def get_trades(self) -> AsyncIterator[Trade]:
        """
        Receives messages from the websocket and yields Trade objects.
        If the message is not a trade message or is malformed, it skips it.
        """
        if not self.ws:
            raise RuntimeError("Websocket not connected. Call connect() first.")

        while True:
            try:
                message = await self.ws.recv()
                response = json.loads(message)

                if not is_trade(response):
                    continue

                trades = response.get("data", [])
                for trade in trades:
                    try:
                        kraken_trade = KrakenTrade.model_validate(trade)
                        yield kraken_trade.into()
                    except ValidationError as e:
                        logger.error(f"Error validating trade: {e}")

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


async def process_trades(
    kraken: KrakenWebsocketAPI, messagebus: QuixApp, topic_name: str
):
    """
    Background task that processes trades from the websocket connection.
    """
    topic = messagebus.topic(name=topic_name, value_serializer="json")
    try:
        with messagebus.get_producer() as producer:
            async for trade in kraken.get_trades():
                message = topic.serialize(
                    key=trade.pair,
                    value=trade.serialize(),
                )
                producer.produce(topic=topic.name, value=message.value, key=message.key)
                logger.info(f"Produced trade: {trade}")

    except asyncio.CancelledError:
        logger.info("Trade processing task was cancelled")
        raise
    except Exception as e:
        logger.error(f"Error processing trades: {e}")
    finally:
        logger.info("Trade processing task has terminated")
