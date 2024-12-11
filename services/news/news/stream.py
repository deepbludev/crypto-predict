import quixstreams as qs
from loguru import logger


def run_stream(stream_app: qs.Application):
    """Builds the stream and runs it."""

    try:
        logger.info("Starting the news stream")
        stream_app.run()
    except Exception as e:
        logger.error(f"Error in Quix Streams thread: {e}")
    finally:
        logger.info("Stream application stopped")
