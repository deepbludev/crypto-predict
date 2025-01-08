import quixstreams as qs
from loguru import logger

from price_predictions.core.settings import price_predictions_settings
from price_predictions.predictor import PricePredictor


def run_stream(stream_app: qs.Application):
    """Builds the stream and runs it."""

    generate_predictions_and_store_in_elastic_search(stream_app)
    try:
        logger.info("Starting the features stream")
        stream_app.run()
    except Exception as e:
        logger.error(f"Error in Quix Streams thread: {e}")
    finally:
        logger.info("Stream application stopped")


def generate_predictions_and_store_in_elastic_search(
    stream_app: qs.Application,
):
    """
    Generates features from the input topic and loads them to the feature store.
    """
    input_topic = price_predictions_settings().input_topic
    predictor = PricePredictor(settings=price_predictions_settings())
    (
        stream_app.dataframe(stream_app.topic(input_topic, value_deserializer="json"))
        .apply(lambda _: predictor.predict())
        .apply(lambda prediction: logger.info(f"Prediction: {prediction.unpack()}"))
        # .sink(fs)
    )

    return stream_app
