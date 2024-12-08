from contextlib import asynccontextmanager

import quixstreams as qs
from fastapi import FastAPI
from loguru import logger

from candles.core.settings import candles_settings
from candles.stream import generate_candles_from_trades
from domain.trades import Trade

print(Trade)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles the lifespan of the FastAPI app.
    """
    await startup(app)
    yield
    await shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "OK"}


async def startup(app: FastAPI):
    """Handles the startup of the messagebus connection."""
    settings = candles_settings()

    # 1. Start the stream
    stream_app = qs.Application(
        broker_address=settings.broker_address,
        consumer_group=settings.consumer_group,
    )
    logger.info(
        f"Connected to messagebus at {settings.broker_address}, "
        f"consumer group: {settings.consumer_group}"
    )

    # 2. Start the stream
    generate_candles_from_trades(stream_app).run()


async def shutdown():
    """Handles the shutdown of the messagebus connection."""
    pass
