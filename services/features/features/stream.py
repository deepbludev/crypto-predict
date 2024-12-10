import quixstreams as qs
from loguru import logger

from features.core.settings import features_settings


def run_stream(stream_app: qs.Application):
    """Builds the stream and runs it."""

    generate_features_from_candles_and_load_to_feature_store(stream_app)
    try:
        logger.info("Starting the features stream")
        stream_app.run()
    except Exception as e:
        logger.error(f"Error in Quix Streams thread: {e}")
    finally:
        logger.info("Stream application stopped")


def generate_features_from_candles_and_load_to_feature_store(
    stream_app: qs.Application,
):
    """
    Generates features from candles and loads them to the feature store.
    """
    settings = features_settings()

    # 1. Read the candles from the messagebus
    stream_app.dataframe(
        topic=stream_app.topic(
            name=settings.input_topic,
            value_deserializer="json",
        )
    ).update(lambda candle: logger.info(f"Current candle: {candle}"))
