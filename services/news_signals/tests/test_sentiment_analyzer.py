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
        pytest.param(
            """
            SEC approves Bitcoin ETF. Unprecedented move to boost crypto adoption
            for all cryptos.
            """,
            BULLISH,
            BULLISH,
            BULLISH,
            id="Case 1: All assets are bullish",
        ),
        pytest.param(
            """
            SEC rejects Bitcoin ETF. Expected to hurt crypto adoption for all
            cryptos.
            """,
            BEARISH,
            BEARISH,
            BEARISH,
            id="Case 2: All assets are bearish",
        ),
        pytest.param(
            """
            Bitcoin price is up 10% today.
            BTC is expected to continue its bullish trend.
            Nevertheless, XRP is not looking so good as BTC.
            """,
            BULLISH,
            NEUTRAL,
            BEARISH,
            id="Case 3: BTC is bullish, ETH is neutral, XRP is bearish",
        ),
        pytest.param(
            # Case 4: BTC and ETH are bullish, XRP neutral
            """
            Ethereum and Bitcoin show strong momentum as Layer 1 solutions gain
            traction. ETH 2.0 staking hits new highs while BTC hashrate reaches
            record levels.
            """,
            BULLISH,
            BULLISH,
            NEUTRAL,
            id="Case 4: BTC and ETH are bullish, XRP neutral",
        ),
        pytest.param(
            """
            SEC investigation into Ethereum's security status creates uncertainty.
            Ripple faces new legal challenges. Bitcoin trades sideways.
            """,
            NEUTRAL,
            BEARISH,
            BEARISH,
            id="Case 5: BTC neutral, ETH and XRP bearish",
        ),
        pytest.param(
            """
            Ethereum surges on successful network upgrade.
            Meanwhile, Bitcoin consolidates at current levels.
            Ripple (XRP) drops 5% on profit taking.
            """,
            NEUTRAL,
            BULLISH,
            BEARISH,
            id="Case 6: Mixed with emphasis on ETH",
        ),
        pytest.param(
            """
            New regulations target XRP and other altcoins specifically.
            Bitcoin remains unaffected due to commodity classification.
            ETH community debates potential regulatory impact.
            """,
            NEUTRAL,
            BEARISH,
            BEARISH,
            id="Case 7: Regulatory news affecting specific assets",
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

    if not (
        (result.btc, result.eth, result.xrp)
        == (expected_btc, expected_eth, expected_xrp),
    ):
        pytest.fail(f"""
        Story: {story}

        BTC:
            Result: {result.btc}
            Expected: {expected_btc}

        ETH:
            Result: {result.eth}
            Expected: {expected_eth}

        XRP:
            Result: {result.xrp}
            Expected: {expected_xrp}

        Reasoning: {result.reasoning}
        """)
