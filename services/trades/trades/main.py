import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger
from trades.core.settings import trades_settings
from trades.kraken import KrakenWebsocketAPI, process_trades


@asynccontextmanager
async def lifespan(app: FastAPI):
    kraken_client, trade_task = await startup(app)
    yield
    await shutdown(kraken_client, trade_task)


async def startup(app: FastAPI):
    """
    Handles the startup of the Kraken websocket connection
    and the background task to process trades.
    """
    # Connect to the Kraken websocket
    settings = trades_settings()
    kraken_client = KrakenWebsocketAPI(settings.symbols)
    await kraken_client.connect()

    # Start the background task to process trades
    trade_task = asyncio.create_task(process_trades(kraken_client))

    return kraken_client, trade_task


async def shutdown(kraken_client: KrakenWebsocketAPI, trade_task: asyncio.Task[None]):
    """
    Handles the shutdown of the Kraken websocket connection
    and the background task to process trades.
    """
    # Shutdown:
    # 1. Close the Kraken websocket connection
    if kraken_client.ws:
        await kraken_client.ws.close()

    # 2. Cancel the background task
    trade_task.cancel()
    try:
        await trade_task
    except asyncio.CancelledError:
        logger.info("Trade processing task was cancelled")


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "OK"}
