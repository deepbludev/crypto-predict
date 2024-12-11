from __future__ import annotations

from enum import Enum

from domain.core import Schema


class NewsOutlet(str, Enum):
    """
    Represents a news outlet from which news stories are obtained.
    """

    CRYPTOPANIC = "cryptopanic"


class NewsStory(Schema):
    """
    Represents a news story, obtained from a news outlet.
    """

    outlet: NewsOutlet
    title: str
    source: str
    published_at: str
    url: str
