import quixstreams as qs
from loguru import logger

from price_predictions.core.settings import price_predictions_settings


def run_stream(stream_app: qs.Application):
    """Builds the stream and runs it."""

    stream_features_and_load_to_feature_store(stream_app)
    try:
        logger.info("Starting the features stream")
        stream_app.run()
    except Exception as e:
        logger.error(f"Error in Quix Streams thread: {e}")
    finally:
        logger.info("Stream application stopped")


def stream_features_and_load_to_feature_store(
    stream_app: qs.Application,
):
    """
    Generates features from the input topic and loads them to the feature store.
    """
    input_topic = price_predictions_settings().input_topic
    (
        stream_app.dataframe(
            stream_app.topic(input_topic, value_deserializer="json")
        ).update(
            lambda f: logger.info(
                f"[{input_topic}] Generating price predictions: {f.get('timestamp')}"
            )
        )
        # .sink(fs)
    )

    return stream_app
