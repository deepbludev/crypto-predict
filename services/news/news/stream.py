import quixstreams as qs
from loguru import logger

from domain.news import NewsStory
from news.core.settings import news_settings
from news.outlets import get_news_outlet_source


def run_stream(stream_app: qs.Application):
    """Builds the stream and runs it."""

    stream_latest_news_from_cryptopanic(stream_app)

    try:
        logger.info("Starting the news stream")
        stream_app.run()
    except Exception as e:
        logger.error(f"Error in Quix Streams thread: {e}")
    finally:
        logger.info("Stream application stopped")


def stream_latest_news_from_cryptopanic(stream_app: qs.Application):
    news_topic = news_settings().news_topic
    cryptopanic_outlet = get_news_outlet_source()
    (
        stream_app.dataframe(source=cryptopanic_outlet)
        .apply(NewsStory.parse)
        .update(
            lambda story: logger.info(
                f"{story.outlet} News story: '{story.title}' "
                f"published at {story.published_at}"
            )
        )
        .apply(NewsStory.serialize)
        .to_topic(stream_app.topic(name=news_topic, value_serializer="json"))
    )
    return stream_app
