from loguru import logger
from quixstreams.sources.base import Source

from domain.news import NewsIngestionMode
from news.core.settings import news_settings
from news.outlets.cryptopanic import (
    CryptoPanicOutletHistoricalSource,
    CryptoPanicOutletLiveSource,
)


def get_news_outlet_source() -> Source:
    ingestion_mode = news_settings().news_ingestion_mode

    match ingestion_mode:
        case NewsIngestionMode.LIVE:
            logger.info("Using live news ingestion")
            return CryptoPanicOutletLiveSource()

        case NewsIngestionMode.HISTORICAL:
            logger.info("Using historical news ingestion")
            return CryptoPanicOutletHistoricalSource()
