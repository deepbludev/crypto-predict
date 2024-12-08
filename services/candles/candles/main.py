import asyncio
from contextlib import asynccontextmanager

import quixstreams as qs
from fastapi import FastAPI
from loguru import logger

from candles.core.settings import candles_settings
from candles.stream import run_stream


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles the lifespan of the FastAPI app.
    """
    stream_task = await startup(app)
    yield
    await shutdown(stream_task)


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

    # 3. Start the stream as a background task
    stream_task = asyncio.create_task(run_stream(stream_app))
    return stream_task


async def shutdown(stream_task: asyncio.Task[None] | None = None):
    """Handles the shutdown of the messagebus connection."""
    if not stream_task:
        return

    # 1. Cancel the background task
    stream_task.cancel()
    try:
        await stream_task
    except asyncio.CancelledError:
        logger.info("Candles processing task was cancelled")
