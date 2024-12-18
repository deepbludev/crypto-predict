from __future__ import annotations

from datetime import datetime, timezone
from time import sleep
from typing import Any, cast

import pandas as pd
import requests
from loguru import logger
from quixstreams.sources.base import Source, StatefulSource

from domain.core import iso_to_timestamp
from domain.news import NewsOutlet, NewsStory
from news.core.settings import news_settings


class CryptoPanicOutletLiveSource(StatefulSource):
    """
    A live source that fetches news from the Cryptopanic API and produces
    news stories to a Kafka topic using Quix Streams.

    It uses the Cryptopanic API to poll for news stories and produce them to a
    Kafka topic using Quix Streams whenever new stories are available.
    """

    def __init__(
        self,
        polling_interval_sec: int = 10,
    ):
        self.client = CryptoPanicClient()
        self.polling_interval_sec = polling_interval_sec
        super().__init__(name="cryptopanic_live")

    def run(self):
        last = self.state.get("last", None)

        while self.running:
            # get latest news from cryptopanic
            stories = self.client.get_news()
            logger.info(f"Last news published at: {last}")

            # keep only the stories that were published after the last one
            if last is not None:
                stories = [s for s in stories if s.published_at > last]

            # serialize and produce the news stories
            for story in stories:
                message = self.serialize(key="news", value=story.unpack())
                self.produce(key=message.key, value=message.value)

            # update the last published news
            if stories:
                last = stories[-1].published_at

            # update the state and flush
            self.state.set("last", last)
            self.flush()

            # wait for the next polling
            sleep(self.polling_interval_sec)


class CryptoPanicClient:
    """
    An HTTP client for the Cryptopanic API. Used to fetch news from the API
    and parse it into news stories.
    """

    def __init__(self):
        settings = news_settings()
        self.url = settings.cryptopanic_news_endpoint
        self.api_key = settings.cryptopanic_api_key
        self.outlet = NewsOutlet.CRYPTOPANIC

    def get_news(self) -> list[NewsStory]:
        """
        Fetches news from the Cryptopanic API, polling the API until
        there are no more news.
        """
        stories: list[NewsStory] = []
        url = f"{self.url}?auth_token={self.api_key}"

        while True:
            batch, next_url = self.get_news_batch(url)
            stories += batch
            logger.info(f"[{self.outlet}] Fetched {len(batch)} news items")

            if not batch or not next_url:
                break

            url = next_url

        return sorted(stories, key=lambda x: x.published_at, reverse=False)

    def get_news_batch(self, url: str) -> tuple[list[NewsStory], str]:
        """
        Fetches a batch of news from the Cryptopanic API.

        Returns:
            A tuple containing the list of news and the next URL to fetch from.
        """
        empty_batch_to_retry: tuple[list[NewsStory], str] = ([], url)

        try:
            response = requests.get(url)
            data = response.json()

        except Exception as e:
            logger.error(f"[{self.outlet}] Error fetching news: {e}")
            sleep(1)
            # return an empty list and the same URL to try again
            return empty_batch_to_retry

        results = data.get("results", [])
        if not results:
            logger.warning(f"[{self.outlet}] Malformed API response: {data}")
            return empty_batch_to_retry

        # parse the data into news stories
        story_batch = [
            NewsStory(
                outlet=NewsOutlet.CRYPTOPANIC,
                title=post["title"],
                published_at=post["published_at"],
                source=post["domain"],
                url=post["url"],
            )
            for post in results
        ]

        # extract the next URL for pagination
        next_url = data["next"]
        return story_batch, next_url


class CryptoPanicOutletHistoricalSource(Source):
    """
    A historical source that reads news from a CSV file and produces
    news stories to a Kafka topic using Quix Streams.
    """

    def __init__(
        self,
    ):
        settings = news_settings()
        self.filepath = settings.cryptopanic_historical_news_filepath
        super().__init__(name="cryptopanic_historical")

    def run(self):
        while self.running:
            df = pd.read_csv(self.filepath).dropna()
            rows = (cast(dict[str, Any], row.to_dict()) for _, row in df.iterrows())  # type: ignore

            for row in rows:
                story = self._row_to_story(row)
                message = self.serialize(key="news", value=story.unpack())
                self.produce(key=message.key, value=message.value)

    def _row_to_story(self, row: dict[str, Any]) -> NewsStory:
        published_at = (
            datetime.strptime(row["newsDatetime"], "%m/%d/%Y %H:%M")
            .replace(tzinfo=timezone.utc)
            .isoformat()
        )
        timestamp = iso_to_timestamp(published_at)

        return NewsStory(
            outlet=NewsOutlet.CRYPTOPANIC,
            title=str(row["title"]),
            published_at=published_at,
            timestamp=timestamp,
            source=str(row["sourceId"]),
            url=str(row["url"]),
        )
