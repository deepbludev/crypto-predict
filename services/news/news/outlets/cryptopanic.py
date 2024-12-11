from __future__ import annotations

from datetime import datetime
from time import sleep

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
            stories: list[NewsStory] = self.client.get_news()
            logger.info(f"Last news published at: {last}")

            # keep only the stories that were published after the last one
            if last is not None:
                stories = [story for story in stories if story.published_at > last]

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
        self.url = news_settings().cryptopanic_news_endpoint

    def get_news(self) -> list[NewsStory]:
        stories = [
            NewsStory(
                outlet=NewsOutlet.CRYPTOPANIC,
                title="test",
                source="crypto.com",
                url="https://cryptopanic.com/news/12345",
                published_at=datetime.now().isoformat(),
            )
            for _ in range(10)
        ]

        return stories
