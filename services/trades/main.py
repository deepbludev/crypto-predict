import asyncio

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from loguru import logger
from trades.core.settings import trades_settings
from trades.kraken import KrakenWebsocketAPI, process_kraken_trades

app = FastAPI()


# Dependency to get the Kraken client from app.state
def get_kraken_client() -> KrakenWebsocketAPI:
    return app.state.kraken_client


# Dependency to get the background task from app.state
def get_trade_task() -> asyncio.Task[None]:
    return app.state.trade_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    # 1. Initialize the Kraken client
    settings = trades_settings()
    kraken_client = KrakenWebsocketAPI(settings.symbols)
    await kraken_client.connect()

    # 2. Start the background task to process trades and store it in app.state
    trade_task = asyncio.create_task(process_kraken_trades(kraken_client))

    yield

    # Shutdown:
    # 1. Close the Kraken websocket connection
    kraken_client: KrakenWebsocketAPI = kraken_client
    if kraken_client.ws:
        await kraken_client.ws.close()

    # Cancel the background task
    trade_task.cancel()
    try:
        await trade_task
    except asyncio.CancelledError:
        logger.info("Trade processing task was cancelled")


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy"}
