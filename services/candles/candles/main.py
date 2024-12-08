from contextlib import asynccontextmanager
from multiprocessing import Process

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
    await startup(app)
    yield
    await shutdown(app)


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "OK"}


async def startup(app: FastAPI):
    """Handles the startup of the messagebus connection."""
    settings = candles_settings()

    # 1. Init the stream application
    app.state.stream_app = qs.Application(
        broker_address=settings.broker_address,
        consumer_group=settings.consumer_group,
    )
    logger.info(
        f"Connected to messagebus at {settings.broker_address}, "
        f"consumer group: {settings.consumer_group}"
    )

    # 2. Start the stream as a parallel process
    app.state.stream_proc = Process(
        target=run_stream,
        args=(app.state.stream_app,),
    )
    app.state.stream_proc.start()


async def shutdown(app: FastAPI):
    """Handles the shutdown of the messagebus connection."""

    # Stop the stream application
    if stream_app := app.state.stream_app:
        try:
            stream_app.stop()
            logger.info("Stream application stopped")
        except Exception as e:
            logger.error(f"Error stopping stream application: {e}")

    # Wait for the process to finish
    if stream_proc := app.state.stream_proc:
        try:
            stream_proc.terminate()
            stream_proc.join(timeout=10)
            if stream_proc.is_alive():
                logger.warning("Stream process did not terminate within timeout")
                stream_proc.kill()  # Force kill if it didn't terminate gracefully
        except Exception as e:
            logger.error(f"Error cleaning up stream process: {e}")
