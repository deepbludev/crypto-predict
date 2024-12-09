import quixstreams as qs
from loguru import logger

from domain.ta import TechnicalAnalysis
from features.core.settings import features_settings
from features.sinks.hopsworks import HopsworksFeatureStoreSink


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
    ta_topic = features_settings().input_topic
    fs = HopsworksFeatureStoreSink().connect()
    (
        stream_app.dataframe(stream_app.topic(ta_topic, value_deserializer="json"))
        .apply(TechnicalAnalysis.parse)
        .update(lambda ta: logger.info(f"Loading TA to feature store: {ta.key()}"))
        .apply(TechnicalAnalysis.serialize)
        .sink(fs)
    )

    return stream_app
