from typing import Any

import quixstreams as qs
from loguru import logger

from candles.core.settings import candles_settings
from domain.candles import Candle
from domain.trades import Trade


def run_stream(stream_app: qs.Application):
    """Builds the stream and runs it."""

    generate_candles_from_trades(stream_app)

    try:
        logger.info("Starting the candles stream")
        stream_app.run()
    except Exception as e:
        logger.error(f"Error in Quix Streams thread: {e}")
    finally:
        logger.info("Stream application stopped")


def generate_candles_from_trades(stream_app: qs.Application):
    """
    Generates candles from trades.

    It consumes trades from the messagebus and produces candles using the
    given timeframe to the messagebus.
    """
    settings = candles_settings()

    def extract_ts(
        value: Any,
        headers: list[tuple[str, bytes]] | None,
        timestamp: float,
        timestamp_type: qs.models.TimestampType,
    ) -> int:
        return value["timestamp"]

    (
        stream_app.dataframe(
            topic=stream_app.topic(
                settings.input_topic,
                timestamp_extractor=extract_ts,
            )
        )
        .apply(lambda trade: Trade.parse(trade or {}))
        # reduce trades into candles using tumbling windows and emit the partial candle
        .tumbling_window(duration_ms=settings.timeframe.to_sec() * 1000)
        .reduce(
            # initialize the candle with the first trade
            initializer=lambda trade: Candle.init(settings.timeframe, trade).unpack(),
            # update the candle with the next trade
            reducer=lambda candle, trade: Candle.parse(candle).update(trade).unpack(),
        )
        .current()
        # close the candle window
        .apply(
            lambda result: Candle.parse(result["value"])
            .close_window(result["start"], result["end"])
            .unpack()
        )
        .to_topic(stream_app.topic(name=settings.output_topic))
        .update(log_candle)
    )

    return stream_app


def log_candle(candle: dict[str, Any]):
    """Log the candle."""
    candle_str = f"{candle['symbol']}-{candle['timeframe']}-{candle['timestamp']}"
    logger.info("Candle: " + candle_str)
