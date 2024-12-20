from typing import Any

import quixstreams as qs
from loguru import logger

from features.core.settings import features_settings
from features.sinks.hopsworks import HopsworksFeatureStoreSink


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
    input_topic = features_settings().input_topic
    fs = HopsworksFeatureStoreSink().connect()
    (
        stream_app.dataframe(stream_app.topic(input_topic, value_deserializer="json"))
        .apply(replace_none_with_zero)
        .update(lambda f: logger.info(f"[{input_topic}] Loading feature: {f}"))
        .sink(fs)
    )

    return stream_app


def replace_none_with_zero(f: dict[str, Any]) -> dict[str, Any]:
    """Replace None values with 0."""
    return {k: 0 if v is None else v for k, v in f.items()}
