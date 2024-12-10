import asyncio
import json
from datetime import datetime
from typing import Any, AsyncIterator, Self, cast

import httpx
import websockets
from loguru import logger
from pydantic import Field, ValidationError, field_serializer
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from domain.core import Schema
from domain.trades import Exchange, Symbol, Trade

from .client import TradesRestClient, TradesWsClient

type KrakenRestResponseTrade = tuple[
    str,  # price
    str,  # qty
    float,  # timestamp in seconds
    str,  # buy/sell
    str,  # market/limit
    str,  # misc
    int,  # ordertxid
]


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
    def from_rest(cls, symbol: str, trade: KrakenRestResponseTrade) -> Self:
        return cls(
            symbol=symbol,
            price=float(trade[0]),
            qty=float(trade[1]),
            timestamp=datetime.fromtimestamp(float(trade[2])),
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
        super().__init__(
            exchange=Exchange.KRAKEN,
            url=url,
            symbols=symbols,
        )

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
            f"[{self.exchange}] Subscribed to {[s.value for s in self.symbols]}"
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

                match channel := res.get("channel"):
                    case "trade":
                        trades = res.get("data", [])
                        for trade in trades:
                            try:
                                yield KrakenTrade.parse(trade).into()
                            except ValidationError as e:
                                msg = f"[{self.exchange}] Error validating trade: {e}"
                                logger.error(msg)
                    case _:
                        logger.info(f"[{self.exchange}] {channel}")

            except ConnectionClosedOK:
                # Normal closure
                logger.info(f"[{self.exchange}] WebSocket connection closed normally")
                break
            except ConnectionClosedError as e:
                # Abnormal closure
                logger.error(
                    f"[{self.exchange}] WebSocket connection closed with error: {e}"
                )
                break
            except Exception as e:
                logger.error(f"[{self.exchange}] Error processing message: {e}")
                continue


class KrakenTradesRestClient(TradesRestClient):
    """
    Kraken REST TradesAPI implementation using async http client.
    """

    def __init__(self, symbols: list[Symbol], url: str):
        """
        Initializes the Kraken REST API with the given symbols,
        converting them to the format expected by the Kraken API.
        """
        self.kraken_symbols = list(map(KrakenTrade.to_kraken_symbol, symbols))
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=30.0))
        super().__init__(
            exchange=Exchange.KRAKEN,
            url=url,
            symbols=symbols,
        )

    async def stream_trades(self, since: datetime) -> AsyncIterator[Trade]:
        """
        Streams trades from the exchange for all symbols concurrently, starting
        from the given datetime, and stopping when no more trades are found.
        """

        since_ns = int(since.timestamp() * 1_000_000_000)  # nanoseconds
        # fetch trades for each symbol concurrently
        results = await asyncio.gather(
            *(
                self.fetch_all_trades(symbol, since_ns)
                for symbol in self.kraken_symbols
            ),
            return_exceptions=True,
        )
        symbol_results = list(zip(self.kraken_symbols, results, strict=False))

        # log errors and continue
        if errors := [
            (symbol, e) for symbol, e in symbol_results if isinstance(e, Exception)
        ]:
            for symbol, e in errors:
                logger.error(f"[{self.exchange}] ({symbol}) Error fetching trades: {e}")

        # collect all trades
        trades = (
            cast(Trade, trade)
            for result in results
            if not isinstance(result, Exception)
            for trade in result  # type: ignore
        )

        # sort trades by timestamp and yield
        for trade in sorted(trades, key=lambda t: t.timestamp):
            yield trade

    async def fetch_all_trades(self, kraken_symbol: str, since: int):
        """
        Fetches all historical trades for a given symbol from the exchange.
        It iterates the fetching until no more trades are found.
        """
        headers = {"Accept": "application/json"}

        async def fetch_trades(kraken_symbol: str, last: int):
            # fetch trades from the exchange
            params = {"pair": kraken_symbol, "since": last}
            res = await self.client.get(self.url, params=params, headers=headers)
            data = res.json()

            # Check for error response
            if "error" in data and data["error"]:
                raise ValueError(f"API error: {data['error']}")

            if "result" not in data:
                raise ValueError(f"Unexpected API response format: {data}")

            # extract data and last trade timestamp
            trades_data, last = data["result"][kraken_symbol], data["result"]["last"]
            last_on = datetime.fromtimestamp(float(last) / 1e9)

            logger.info(
                f"[{self.exchange}] {kraken_symbol}: "
                f"Fetched {len(trades_data)} historical trades. "
                f"Last trade on: {last_on} ({last} ns)"
            )

            # return converted Trade objects
            trades = [
                KrakenTrade.from_rest(kraken_symbol, trade).into()
                for trade in trades_data
            ]

            return last, trades

        fetched_trades: list[Trade] = []
        last = since
        while True:
            last, trades = await fetch_trades(kraken_symbol, last)
            await asyncio.sleep(1)  # avoid rate limiting
            fetched_trades.extend(trades)
            if not trades:
                break
        return fetched_trades
