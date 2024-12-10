import asyncio
from datetime import datetime

import quixstreams as qs
from loguru import logger

from trades.core.settings import trades_settings
from trades.exchanges.client import TradesWsClient


async def consume_live_trades(
    stream_app: qs.Application,
    exchange_client: TradesWsClient,
    live_trades_active: bool,
):
    """
    Async task that consumes live trades from the exchange websocket API and
    produces them to the messagebus.

    It runs continuously, until the service is stopped.
    """
    settings = trades_settings()
    if not live_trades_active:
        return

    topic = stream_app.topic(name=settings.topic, value_serializer="json")
    try:
        with stream_app.get_producer() as producer:
            async for trade in exchange_client.stream_trades():
                message = topic.serialize(
                    key=trade.symbol,
                    value=trade.unpack(),
                )
                producer.produce(topic=topic.name, value=message.value, key=message.key)
                logger.info(
                    f"[{trade.exchange.value}] Live Trade: "
                    f"{trade.symbol.value} {trade.price} "
                    f"({datetime.fromtimestamp(trade.timestamp/1000)})"
                )

    except asyncio.CancelledError:
        logger.info(f"[{exchange_client.name}] Trade processing task was cancelled")
        raise
    except Exception as e:
        logger.error(f"[{exchange_client.name}] Error processing trades: {e}")
    finally:
        logger.info(f"[{exchange_client.name}] Trade processing task has terminated")


async def consume_historical_trades(
    stream_app: qs.Application,
    # TODO: exchange client
    since: datetime | None = None,
):
    """
    Async task that consumes historical trades from the given exchange and
    produces them to the messagebus.

    It runs until the historical trades are exhausted.
    """
    if not since:
        return

    ns = int(since.timestamp() * 1_000_000_000)  # nanoseconds
    logger.info(f"Consuming historical trades from Kraken since {since} ({ns} ns)")

    # TODO: Implement
    pass
