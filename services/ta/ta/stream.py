import quixstreams as qs
from loguru import logger

from domain.candles import Candle
from ta.core.settings import ta_settings


def perform_ta_from_candles(stream_app: qs.Application):
    """
    Generates technical indicators from candles.

    It consumes candles from the messagebus and produces
    technical indicators to the messagebus.
    """
    settings = ta_settings()
    (
        # 1. Read the candles from the messagebus
        stream_app.dataframe(
            topic=stream_app.topic(
                name=settings.input_topic,
                value_deserializer="json",
            )
        )
        # 2. Validate the candle
        # .update(lambda candle: logger.info(f"Received candle: {candle}"))
        .apply(lambda candle: Candle.model_validate(candle or {}))
        # 3. Generate technical indicators
        .apply(
            # TODO: Implement technical indicators
            lambda candle: {
                "ta": {
                    "candle": candle.unpack(),
                },
            }
        )
        # 4. Produce the technical indicators to the output topic
        .to_topic(
            stream_app.topic(
                name=settings.output_topic + "_debug",  # TODO: Remove debug
                value_serializer="json",
            )
        )
        .update(lambda ta: logger.info(f"Produced ta: {ta}"))
    )

    return stream_app
