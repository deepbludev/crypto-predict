from contextlib import asynccontextmanager

from fastapi import FastAPI

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
    """
    Simple health check endpoint.
    """
    return {"status": "OK"}


async def startup(app: FastAPI):
    """
    Handles the startup of the Kraken websocket connection
    and the background task to process trades.
    """
    pass


async def shutdown():
    """
    Handles the shutdown of the Kraken websocket connection
    and the background task to process trades.
    """
    pass
