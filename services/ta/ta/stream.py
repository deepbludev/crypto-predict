from typing import Any, cast

import quixstreams as qs
from loguru import logger

from domain.candles import Candle
from ta.core.settings import ta_settings

MAX_CANDLES_IN_STATE = ta_settings().max_candles_in_state


def run_stream(stream_app: qs.Application):
    """Builds the stream and runs it."""
    perform_ta_from_candles(stream_app)

    try:
        logger.info("Starting the TA stream")
        stream_app.run()
    except Exception as e:
        logger.error(f"Error in Quix Streams thread: {e}")
    finally:
        logger.info("Stream application stopped")


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
        .apply(lambda candle: Candle.model_validate(candle or {}))
        # TODO: filter out candles that are not of the same window size
        # 3. Update the candle state with the latest candle
        .apply(update_candle_state_with_latest, stateful=True)
        # 4. Generate technical indicators
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
            topic=stream_app.topic(
                name=settings.output_topic + "_debug",  # TODO: Remove debug
                value_serializer="json",
            )
        )
        .update(lambda ta: logger.info(f"Produced ta: {ta}"))
    )

    return stream_app


def update_candle_state_with_latest(latest: Candle, state: qs.State) -> Candle:
    """
    Updates the candles in the state using the latest candle.

    If the latest candle belongs to a new window, and the total number
    of candles in the state is less than the max number of candles to keep,
    then it is appended to the list.

    If it belongs to the current window, then it replaces the last candle in the list.

    Args:
        candle: The latest candle
        state: The state of our quix stream application
        max_candles_in_state: The maximum number of candles to keep in the state
    Returns:
        None
    """
    # Get the list of candles from our state
    candles_state = cast(list[dict[str, Any]], state.get("candles", default=[]))
    last_candle = Candle.model_validate(candles_state[-1]) if candles_state else None

    if latest.same_window(last_candle):
        # Replace the last candle in the list with the latest candle
        candles_state[-1] = latest.unpack()
    else:
        # Append if the state is empty or the candle is not in the same window
        candles_state.append(latest.unpack())

    # If the total number of candles in the state is greater than the maximum number of
    # candles allowed, the oldest candle is removed from the list
    if len(candles_state) > MAX_CANDLES_IN_STATE:
        candles_state.pop(0)

    # TODO: check if the candles have no missing windows
    # this can happen for low volume pairs. In this case, the missing windows
    # should be interpolated.

    logger.debug(f"Candles in state for {latest.symbol}: {len(candles_state)}")

    # Update the state with the new list of candles
    state.set("candles", candles_state)

    return latest
