import asyncio
from datetime import datetime

import quixstreams as qs
from loguru import logger

from trades.core.settings import trades_settings
from trades.exchanges.kraken import KrakenTradesWsClient


async def consume_live_trades_from_kraken(
    kraken_client: KrakenTradesWsClient,
    stream_app: qs.Application,
):
    """
    Background task that consumes live trades from the Kraken websocket API and
    produces them to the messagebus.

    It runs continuously, until the service is stopped.
    """
    settings = trades_settings()
    topic = stream_app.topic(name=settings.topic, value_serializer="json")
    try:
        with stream_app.get_producer() as producer:
            async for trade in kraken_client.stream_trades():
                message = topic.serialize(
                    key=trade.symbol,
                    value=trade.unpack(),
                )
                producer.produce(topic=topic.name, value=message.value, key=message.key)
                logger.info(
                    f"Live Trade ({trade.exchange.value}): "
                    f"{trade.symbol.value} {trade.price} "
                    f"({datetime.fromtimestamp(trade.timestamp/1000)})"
                )

    except asyncio.CancelledError:
        logger.info("Trade processing task from Kraken was cancelled")
        raise
    except Exception as e:
        logger.error(f"Error processing trades: {e}")
    finally:
        logger.info("Trade processing task has terminated")


async def consume_historical_trades_from_kraken(
    stream_app: qs.Application,
):
    """
    Background task that consumes historical trades from the Kraken REST API and
    produces them to the messagebus.

    It runs until the historical trades are exhausted.
    """
    # TODO: Implement
    since = trades_settings().kraken_backfill_trades_since
    if not since:
        return

    ns = since.timestamp() * 1_000_000_000  # nanoseconds
    logger.info(f"Consuming historical trades from Kraken since {since} ({ns} ns)")
    pass
