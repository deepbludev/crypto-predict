import pytest

from domain.llm import LLMModel
from domain.news import NewsOutlet, NewsStory
from domain.sentiment_analysis import SentimentSignal
from news_signals.signals.ollama import OllamaSentimentAnalyzer

BULLISH, NEUTRAL, BEARISH = (
    SentimentSignal.BULLISH,
    SentimentSignal.NEUTRAL,
    SentimentSignal.BEARISH,
)


@pytest.fixture
def ollama_analyzer() -> OllamaSentimentAnalyzer:
    return OllamaSentimentAnalyzer(
        llm_model=LLMModel.LLAMA_3_2_3B,
        base_url="http://localhost:11434",
    )


@pytest.mark.parametrize(
    "story, expected_btc, expected_eth, expected_xrp",
    [
        (
            # case 1: All assets are bullish
            "SEC approves Bitcoin ETF. Unprecedented move to boost crypto adoption for all cryptos.",  # noqa: E501
            BULLISH,
            BULLISH,
            BULLISH,
        ),
        (
            # case 2: All assets are bearish
            "SEC rejects Bitcoin ETF. Expected to hurt crypto adoption in general.",  # noqa: E501
            BEARISH,
            BEARISH,
            BEARISH,
        ),
        (
            # case 3: BTC is bullish, ETH is neutral, XRP is bearish
            "Bitcoin price is up 10% today. BTC is expected to continue its bullish trend. Not looking so good for XRP.",  # noqa: E501
            NEUTRAL,
            NEUTRAL,
            BEARISH,
        ),
    ],
)
def test_ollama_analyzer(
    ollama_analyzer: OllamaSentimentAnalyzer,
    story: str,
    expected_btc: SentimentSignal,
    expected_eth: SentimentSignal,
    expected_xrp: SentimentSignal,
):
    result = ollama_analyzer.analyze(
        NewsStory(
            outlet=NewsOutlet.CRYPTOPANIC,
            title=story,
            source="crypto.com",
            published_at="2024-01-01",
            url="https://crypto.com/news/dummy-url",
        )
    )
    print(result.reasoning)
    assert result.btc == expected_btc
    assert result.eth == expected_eth
    assert result.xrp == expected_xrp
