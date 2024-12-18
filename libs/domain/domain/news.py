from __future__ import annotations

from enum import Enum

from pydantic import Field

from domain.core import Schema, now_timestamp


class NewsIngestionMode(str, Enum):
    """
    The mode of ingestion of news.

    LIVE: ingest news from a live source
    HISTORICAL: ingest news from a historical source, such as a CSV file
    """

    LIVE = "LIVE"
    HISTORICAL = "HISTORICAL"

    def to_auto_reset_offset_mode(self):
        """Convert the ingestion mode to the auto-reset offset mode, used by kafka."""
        match self:
            case NewsIngestionMode.LIVE:
                return "earliest"
            case NewsIngestionMode.HISTORICAL:
                return "latest"


class NewsOutlet(str, Enum):
    """
    Represents a news outlet from which news stories are obtained.
    """

    CRYPTOPANIC = "CRYPTOPANIC"


class NewsStory(Schema):
    """
    Represents a news story, obtained from a news outlet.
    """

    outlet: NewsOutlet
    title: str
    source: str
    published_at: str
    url: str
    timestamp: int = Field(default_factory=now_timestamp)

    @classmethod
    def dummy(cls, title: str) -> NewsStory:
        return cls(
            outlet=NewsOutlet.CRYPTOPANIC,
            title=title,
            source="dummy",
            published_at="dummy",
            url="dummy",
        )
