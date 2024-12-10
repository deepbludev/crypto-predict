import asyncio
from contextlib import asynccontextmanager

import quixstreams as qs
from fastapi import FastAPI
from loguru import logger

from trades.core.settings import trades_settings
from trades.exchanges.kraken import KrakenTradesWsClient
from trades.stream import (
    consume_historical_trades_from_kraken,
    consume_live_trades_from_kraken,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles the lifespan of the FastAPI app.
    """
    await startup(app)
    yield
    await shutdown(app)


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

    # 2. Connect to the websocket clients
    app.state.ws_clients = [
        kraken_ws := await KrakenTradesWsClient(
            url=settings.kraken_ws_endpoint,
            symbols=settings.symbols,
        ).connect(),
    ]

    # 3. Start the streams as a background tasks
    trade_tasks = [
        # Live trades
        consume_live_trades_from_kraken(kraken_ws, stream_app),
        # Historical trades
        consume_historical_trades_from_kraken(stream_app),
    ]
    app.state.async_tasks = [*map(asyncio.create_task, trade_tasks)]


async def shutdown(app: FastAPI):
    """
    Handles the shutdown of the Kraken websocket connection
    and the background task to process trades.
    """
    # 1. Close the websocket connections
    await asyncio.gather(*[ws.close() for ws in app.state.ws_clients])

    # 2. Cancel the background tasks
    for task in app.state.async_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logger.info(f"Async task was cancelled: {task.get_name()}")
