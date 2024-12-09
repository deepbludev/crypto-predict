from typing import Any, cast

import quixstreams as qs
from loguru import logger

from domain.candles import Candle
from domain.ta import TechnicalAnalysis
from ta.core.settings import ta_settings

MAX_CANDLES_IN_STATE = ta_settings().max_candles_in_state


def run_stream(stream_app: qs.Application):
    """Builds the stream and runs it."""
    do_ta_from_candles(stream_app)

    try:
        logger.info("Starting the TA stream")
        stream_app.run()
    except Exception as e:
        logger.error(f"Error in Quix Streams thread: {e}")
    finally:
        logger.info("Stream application stopped")


def do_ta_from_candles(stream_app: qs.Application):
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
        # 3. Filter out candles that are not compatible with the latest candle
        .filter(is_compatible_with_last_candle_if_any, stateful=True)
        # 4. Update the state with the latest candle
        .apply(update_state_with_latest, stateful=True)
        # 5. Generate technical analysis
        .apply(do_ta_for_latest, stateful=True)
        .apply(lambda ta: ta.unpack())
        # 6. Produce the technical analysis to the output topic
        .to_topic(
            topic=stream_app.topic(
                name=settings.output_topic,
                value_serializer="json",
            )
        )
        .update(lambda ta: logger.info(f"Produced ta: {ta}"))
    )

    return stream_app


def get_candle_state(state: qs.State) -> list[dict[str, Any]]:
    """Gets the candle state from the state."""
    return cast(list[dict[str, Any]], state.get("candles", default=[]))


def get_last_candle(state: qs.State) -> Candle | None:
    """Gets the last candle from the state."""
    candles_state = get_candle_state(state)
    return Candle.model_validate(candles_state[-1]) if candles_state else None


def is_compatible_with_last_candle_if_any(latest: Candle, state: qs.State) -> bool:
    """
    Filters out candles that are not compatible with the latest candle,
    if there is a last candle in the state.
    """
    last_candle = get_last_candle(state)
    return not last_candle or latest.is_compatible(last_candle)


def update_state_with_latest(latest: Candle, state: qs.State) -> Candle:
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
    candles_state = get_candle_state(state)
    last_candle = get_last_candle(state)

    if latest.is_same_window(last_candle):
        # Replace the last candle in the list with the latest candle
        candles_state[-1] = latest.unpack()
    else:
        # Append if the state is empty or the candle is not in the same window
        candles_state.append(latest.unpack())

    if len(candles_state) > MAX_CANDLES_IN_STATE:
        # If the total number of candles in the state is greater than the maximum
        # number of candles allowed, the oldest candle is removed from the list
        candles_state.pop(0)

    # TODO: check if the candles have no missing windows
    # this can happen for low volume pairs. In this case, the missing windows
    # should be interpolated.

    # Update the state with the new list of candles
    state.set("candles", candles_state)

    return latest


def do_ta_for_latest(latest: Candle, state: qs.State) -> TechnicalAnalysis:
    """Generates technical indicators from a list of candles."""
    candles_state = cast(list[dict[str, Any]], state.get("candles", default=[]))

    return TechnicalAnalysis.calc(
        candle=latest,
        high_values=(candle["high"] for candle in candles_state),
        low_values=(candle["low"] for candle in candles_state),
        close_values=(candle["close"] for candle in candles_state),
        volume_values=(candle["volume"] for candle in candles_state),
    )
