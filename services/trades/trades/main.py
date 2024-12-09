import asyncio
from contextlib import asynccontextmanager

import quixstreams as qs
from fastapi import FastAPI
from loguru import logger

from trades.core.settings import trades_settings
from trades.kraken import KrakenWebsocketAPI, process_kraken_trades


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles the lifespan of the FastAPI app.
    """
    kraken_client, trade_task = await startup(app)
    yield
    await shutdown(kraken_client, trade_task)


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "OK"}


async def startup(app: FastAPI):
    """
    Handles the startup of the Kraken websocket connection
    and the background task to process trades.
    """
    settings = trades_settings()

    # 1. Initialize the stream application
    stream_app = qs.Application(
        broker_address=settings.broker_address,
        consumer_group=settings.consumer_group,
    )
    logger.info(
        f"Connected to messagebus at {settings.broker_address}, "
        f"consumer group: {settings.consumer_group}"
    )

    # 2. Connect to the Kraken websocket
    kraken_client = KrakenWebsocketAPI(settings.symbols)
    await kraken_client.connect()

    # 3. Start the stream as a background task
    trade_task = asyncio.create_task(
        process_kraken_trades(
            kraken_client,
            stream_app,
            topic_name=settings.topic,
        )
    )

    return kraken_client, trade_task


async def shutdown(kraken_client: KrakenWebsocketAPI, trade_task: asyncio.Task[None]):
    """
    Handles the shutdown of the Kraken websocket connection
    and the background task to process trades.
    """
    # 1. Close the Kraken websocket connection
    if kraken_client.ws:
        await kraken_client.ws.close()

    # 2. Cancel the background task
    trade_task.cancel()
    try:
        await trade_task
    except asyncio.CancelledError:
        logger.info("Trade processing task was cancelled")
