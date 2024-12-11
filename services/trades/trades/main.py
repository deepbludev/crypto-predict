import asyncio
from contextlib import asynccontextmanager

import quixstreams as qs
from fastapi import FastAPI
from loguru import logger

from trades.core.settings import trades_settings
from trades.exchanges.kraken import KrakenTradesRestClient, KrakenTradesWsClient
from trades.stream import (
    consume_historical_trades,
    consume_live_trades,
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
        kraken_ws := KrakenTradesWsClient(
            url=settings.kraken_ws_endpoint,
            symbols=settings.symbols,
        ),
        # Add other exchanges here...
    ]

    # 3. Connect to the REST clients
    app.state.rest_clients = [
        kraken_rest := KrakenTradesRestClient(
            url=settings.kraken_rest_endpoint,
            symbols=settings.symbols,
        ),
        # Add other exchanges here...
    ]

    # 4. Start the streams as a background tasks
    live_streams = [
        # Kraken
        consume_live_trades(
            stream_app,
            exchange_client=kraken_ws,
            live_trades_active=settings.kraken_consume_live_trades,
        ),
        # Add other exchanges here...
    ]
    historical_streams = [
        # Kraken
        consume_historical_trades(
            stream_app,
            exchange_client=kraken_rest,
            since=settings.kraken_backfill_trades_since,
        ),
        # Add other exchanges here...
    ]

    app.state.async_tasks = [
        *map(
            asyncio.create_task,
            live_streams + historical_streams,
        )
    ]


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
