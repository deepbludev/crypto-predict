import abc
from typing import AsyncIterator, Self

from loguru import logger
from websockets.asyncio.client import ClientConnection

from domain.trades import Symbol, Trade


class TradesWebsocketClient(abc.ABC):
    """
    Abstract base class for websocket clients.
    """

    name: str
    url: str
    symbols: list[Symbol]
    ws: ClientConnection | None

    def __init__(
        self,
        name: str,
        symbols: list[Symbol],
        url: str,
    ):
        """
        Initializes the websocket client with the given symbols,
        converting them to the format expected by the Kraken API.
        """
        self.name = name
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
            logger.info(f"Closing {self.name} websocket connection")
            await self.ws.close()
            self.ws = None
