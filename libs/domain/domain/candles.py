from enum import Enum


class CandleWindowSize(str, Enum):
    WINDOW_1m = "1m"
    WINDOW_5m = "5m"
    WINDOW_15m = "15m"
    WINDOW_30m = "30m"
    WINDOW_1h = "1h"
    WINDOW_4h = "4h"
    WINDOW_1D = "1D"
    WINDOW_1W = "1W"
    WINDOW_1M = "1M"
