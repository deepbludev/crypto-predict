import asyncio
from datetime import datetime

import quixstreams as qs
from loguru import logger

from trades.core.settings import trades_settings
from trades.exchanges.kraken import KrakenWebsocketClient


async def consume_trades_from_kraken_ws(
    kraken_client: KrakenWebsocketClient,
    stream_app: qs.Application,
):
    """
    Background task that processes Kraken trades.
    It uses the Kraken websocket API to get the trades and the Quix messagebus
    to produce them.
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
                    f"Trade ({trade.exchange.value}): "
                    f"{trade.symbol.value} at {trade.price} "
                    f"({datetime.fromtimestamp(trade.timestamp/1000)})"
                )

    except asyncio.CancelledError:
        logger.info("Trade processing task from Kraken was cancelled")
        raise
    except Exception as e:
        logger.error(f"Error processing trades: {e}")
    finally:
        logger.info("Trade processing task has terminated")
