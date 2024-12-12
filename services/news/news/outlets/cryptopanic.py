from __future__ import annotations

from time import sleep

import requests
from loguru import logger
from quixstreams.sources.base import StatefulSource

from domain.news import NewsOutlet, NewsStory
from news.core.settings import news_settings


class CryptoPanicOutlet(StatefulSource):
    def __init__(
        self,
        polling_interval_sec: int = 10,
    ):
        super().__init__(name="cryptopanic")
        self.client = CryptoPanicClient()
        self.polling_interval_sec = polling_interval_sec

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
            logger.debug(f"[{self.outlet}] Fetched {len(batch)} news items")

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
