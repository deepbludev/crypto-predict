import abc
from datetime import datetime
from typing import AsyncIterator, Self

from loguru import logger
from websockets.asyncio.client import ClientConnection

from domain.trades import Exchange, Symbol, Trade


class TradesWsClient(abc.ABC):
    """
    Abstract base class for websocket exchange clients.
    It establishes a websocket connection and subscribes to the exchange's
    trade channel and streams them asynchronously.
    """

    exchange: Exchange
    url: str
    symbols: list[Symbol]
    ws: ClientConnection | None

    def __init__(self, exchange: Exchange, symbols: list[Symbol], url: str):
        """Initializes the websocket client"""
        self.exchange = exchange
        self.url = url
        self.symbols = symbols
        self.ws = None

    @abc.abstractmethod
    async def connect(self) -> Self:
        """
        Establishes the websocket connection and subscribes to trades,
        setting the ws attribute and returning the client instance.
        """
        pass

    def check_connection(self):
        """
        Checks if the websocket connection is established,
        raising a RuntimeError if it is not.
        """
        if self.ws is None:
            raise RuntimeError("Websocket not connected. Call connect() first.")
        return self.ws

    @abc.abstractmethod
    def stream_trades(self) -> AsyncIterator[Trade]:
        """
        Receives messages from the websocket and yields Trade objects.
        If the message is not a trade message or is malformed, it skips it.
        """
        pass

    async def close(self):
        """
        Closes the websocket connection.
        """
        if self.ws:
            logger.info(f"Closing {self.exchange} websocket connection")
            await self.ws.close()
            self.ws = None


class TradesRestClient(abc.ABC):
    """
    Abstract base class for REST exchange clients.
    It fetches historical trades from the exchange via the exchange's REST API
    and streams them asynchronously.
    """

    exchange: str
    url: str
    symbols: list[Symbol]

    def __init__(self, exchange: Exchange, symbols: list[Symbol], url: str):
        """Initializes the REST client"""
        self.exchange = exchange
        self.symbols = symbols
        self.url = url

    @abc.abstractmethod
    def stream_trades(self, since: datetime) -> AsyncIterator[Trade]:
        """
        Fetches historical trades from the exchange since the given datetime and
        yields them as Trade objects asynchronously.
        """
        pass
