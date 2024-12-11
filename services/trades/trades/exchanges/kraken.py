import asyncio
import json
from datetime import datetime
from typing import Any, AsyncIterator, Self

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
                channel = res.get("channel")
                if channel != "trade":
                    logger.info(f"[{self.exchange}] {channel}")
                    continue

                trades = res.get("data", [])
                for trade in trades:
                    try:
                        yield KrakenTrade.parse(trade).into()
                    except ValidationError as e:
                        msg = f"[{self.exchange}] Error validating trade: {e}"
                        logger.error(msg)

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
    Kraken REST TradesAPI implementation using async HTTP client.
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
        Streams trades from the exchange for all symbols sequentially,
        starting from the given datetime, and yielding trades as they are fetched.

        It stops when the current time is reached.
        """
        now = datetime.now()
        for ksym in self.kraken_symbols:
            async for trade in self.stream_trades_for_symbol(
                kraken_symbol=ksym,
                since=since,
                stop=now,
            ):
                yield trade

    async def stream_trades_for_symbol(
        self, kraken_symbol: str, since: datetime, stop: datetime
    ) -> AsyncIterator[Trade]:
        """
        Asynchronously fetches all historical trades for a given symbol
        from the exchange, yielding trades as they are fetched.

        It stops when the stop timestamp is reached.
        """
        exsym_log = f"[{self.exchange}] {kraken_symbol}"
        logger.info(f"{exsym_log}: Fetching trades...")

        # start from the given since timestamp
        since_ns, stop_ns = to_ns(since), to_ns(stop)
        last = since_ns

        # iterate until the current time is reached
        while True:
            # wait 1 sec to avoid rate limiting, recommended in Kraken docs
            await asyncio.sleep(1)

            # fetch trades from the exchange
            headers = {"Accept": "application/json"}
            params = {"pair": kraken_symbol, "since": last}
            res = await self.client.get(self.url, params=params, headers=headers)
            data = res.json()

            result, error = data.get("result"), data.get("error")
            if error:
                raise ValueError(f"API error: {data['error']}")
            if not result:
                raise ValueError(f"Unexpected API response format: {data}")

            # extract data and last trade timestamp
            trades_data = result.get(kraken_symbol, [])
            last = int(result.get("last", last))

            last_on = f"Last trade on: {to_dt(last)} ({last} ns)"
            logger.info(
                f"{exsym_log}: Fetched {len(trades_data)} historical trades. {last_on}"
            )

            if last >= stop_ns:
                # stop if the current time is reached
                logger.info(f"{exsym_log}: Finished fetching trades. {last_on}")
                break

            # yield all the trades
            try:
                for t in trades_data:
                    yield KrakenTrade.from_rest(kraken_symbol, t).into()
            except ValidationError as e:
                logger.error(f"{exsym_log}: " f"Error validating trade: {e}")


def to_ns(dt: datetime) -> int:
    return int(dt.timestamp() * 1_000_000_000)


def to_dt(ns: int) -> datetime:
    return datetime.fromtimestamp(float(ns) / 1_000_000_000)
