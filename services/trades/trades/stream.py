import asyncio
from datetime import datetime

import quixstreams as qs
from loguru import logger

from trades.core.settings import trades_settings
from trades.exchanges.client import TradesRestClient, TradesWsClient


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
    ex, topic = exchange_client.exchange, settings.topic
    if not live_trades_active:
        logger.info(f"[{ex}] Live trades are not active. Skipping...")
        return

    try:
        logger.info(f"[{ex}] Consuming live trades")
        await exchange_client.connect()
        trades_topic = stream_app.topic(name=topic, value_serializer="json")
        with stream_app.get_producer() as producer:
            async for trade in exchange_client.stream_trades():
                msg = trades_topic.serialize(key=trade.symbol, value=trade.unpack())
                producer.produce(topic=trades_topic.name, value=msg.value, key=msg.key)

                logger.info(
                    f"[{trade.exchange}] Live Trade: "
                    f"{trade.symbol.value} {trade.price} "
                    f"({datetime.fromtimestamp(trade.timestamp/1000)})"
                )

    except asyncio.CancelledError:
        logger.info(f"[{ex}] Live Trade processing task was cancelled")
        raise
    except Exception as e:
        logger.error(f"[{ex}] Error processing live trades: {e}")
    finally:
        logger.info(f"[{ex}] Live Trade processing task has terminated")


async def consume_historical_trades(
    stream_app: qs.Application,
    exchange_client: TradesRestClient,
    since: datetime | None = None,
):
    """
    Async task that consumes historical trades from the given exchange and
    produces them to the messagebus.

    It runs until the historical trades before the current time are exhausted.
    """
    settings = trades_settings()
    ex, topic = exchange_client.exchange, settings.topic_historical

    if not since:
        logger.info(f"[{ex}] Historical trades are not active. Skipping...")
        return
    try:
        logger.info(f"[{ex}] Consuming historical trades: {since}")
        topic = stream_app.topic(name=topic, value_serializer="json")

        with stream_app.get_producer() as producer:
            async for trade in exchange_client.stream_trades(since):
                msg = topic.serialize(key=trade.symbol, value=trade.unpack())
                producer.produce(topic=topic.name, value=msg.value, key=msg.key)

                logger.info(
                    f"[{trade.exchange}] Historical Trade: "
                    f"{trade.symbol.value} {trade.price} "
                    f"({datetime.fromtimestamp(trade.timestamp/1000)})"
                )

    except asyncio.CancelledError:
        logger.info(f"[{ex}] Historical Trade task was cancelled")
        raise
    except Exception as e:
        logger.error(f"[{ex}] Error processing historical trades: {e}")
    finally:
        logger.info(f"[{ex}] Historical Trade task has terminated")
