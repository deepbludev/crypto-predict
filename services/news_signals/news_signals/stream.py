import quixstreams as qs
from loguru import logger

from domain.news import NewsStory
from news_signals.core.settings import news_signals_settings
from news_signals.signals import get_sentiment_analyzer


def run_stream(stream_app: qs.Application):
    """Builds the stream and runs it."""
    generate_signal_from_news(stream_app)

    try:
        logger.info("Starting the News Signals stream")
        stream_app.run()
    except Exception as e:
        logger.error(f"Error in Quix Streams thread: {e}")
    finally:
        logger.info("Stream application stopped")


def generate_signal_from_news(stream_app: qs.Application):
    """
    Generates news signals from news using an LLM.

    It consumes news stories from the messagebus and produces
    news signals to the messagebus.
    """
    settings, analyzer = news_signals_settings(), get_sentiment_analyzer()

    (
        stream_app.dataframe(topic=stream_app.topic(name=settings.input_topic))
        .apply(NewsStory.parse)
        .update(lambda story: logger.info(f"Analyzing story: {story.title}"))
        .apply(analyzer.analyze)
        .apply(lambda analysis: analysis.encoded())
        .to_topic(topic=stream_app.topic(name=settings.output_topic))
        .update(lambda analysis: logger.info(f"Produced signal: {analysis}"))
    )

    return stream_app
