import quixstreams as qs
from loguru import logger


def run_stream(stream_app: qs.Application):
    """Builds the stream and runs it."""
    generate_signal_from_news(stream_app)

    try:
        logger.info("Starting the News Signals stream")
        stream_app.run()
    except Exception as e:
        logger.error(f"Error in Quix Streams thread: {e}")
    finally:
        logger.info("Stream application stopped")


def generate_signal_from_news(stream_app: qs.Application):
    """
    Generates news signals from news using an LLM.
    """

    return stream_app
