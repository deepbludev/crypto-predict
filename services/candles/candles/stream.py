from typing import Any

import quixstreams as qs
from loguru import logger

from candles.core.settings import candles_settings
from domain.candles import Candle
from domain.trades import Trade


def extract_ts(
    value: Any,
    headers: list[tuple[str, bytes]] | None,
    timestamp: float,
    timestamp_type: qs.models.TimestampType,
) -> int:
    """
    Specifying a custom timestamp extractor to use the timestamp from the message
    payload instead of Kafka timestamp.
    """
    return value["timestamp"]


def generate_candles_from_trades(stream_app: qs.Application):
    """
    Generates candles from trades.

    It consumes trades from the messagebus and produces candles using the
    given window size to the messagebus.
    """
    settings = candles_settings()
    (
        # 1. Read the trades from the messagebus
        stream_app.dataframe(
            topic=stream_app.topic(
                name=settings.input_topic,
                value_deserializer="json",
                timestamp_extractor=extract_ts,
            )
        )
        # 2. Validate the trade
        .apply(lambda trade: Trade.model_validate(trade or {}))
        # 3. Reduce trades into candles using tumbling windows
        .tumbling_window(duration_ms=settings.window_size.to_sec() * 1000)
        .reduce(
            # 3.1. Initialize the candle with the first trade
            initializer=lambda trade: Candle.init(settings.window_size, trade).unpack(),
            # 3.2. Update the candle with the next trade
            reducer=lambda candle, trade: Candle(**candle).update(trade).unpack(),
        )
        # 4. Emit the partial candle
        .current()
        # 5. Close the candle window using the window start and end timestamps
        .apply(
            lambda res: Candle(**res["value"])
            .close_window(res["start"], res["end"])
            .unpack()
        )
        # 6. Produce the candle to the output topic
        .to_topic(
            stream_app.topic(
                name=settings.output_topic,
                value_serializer="json",
            )
        )
        # 7. Log the produced candle
        .update(lambda candle: logger.info(f"Produced candle: {candle}"))
    )

    return stream_app
