import pytest

from domain.llm import LLMName
from domain.news import NewsOutlet, NewsStory
from domain.sentiment_analysis import Sentiment
from domain.trades import Asset
from news_signals.signals.ollama import OllamaSentimentAnalyzer

BULLISH, BEARISH = Sentiment.BULLISH, Sentiment.BEARISH
BTC, ETH, XRP = Asset.BTC, Asset.ETH, Asset.XRP


@pytest.fixture
def ollama_analyzer() -> OllamaSentimentAnalyzer:
    return OllamaSentimentAnalyzer(
        llm_name=LLMName.LLAMA_3_2_3B,
        base_url="http://localhost:11434",
    )


@pytest.mark.parametrize(
    "story, expected_sentiments",
    [
        pytest.param(
            """
            Decentryk doing some laser engraving testing for a new luxury brand
            customer for our new NFT protocol for Physical…
            """,
            [],
            id="No clear impact",
        ),
        pytest.param(
            """
            SEC approves Bitcoin ETF. Unprecedented move to boost crypto adoption
            for all cryptos.
            """,
            [(BTC, BULLISH), (ETH, BULLISH)],
            id="All assets are bullish",
        ),
        pytest.param(
            """
            SEC rejects Bitcoin ETF. Expected to hurt crypto adoption for all
            cryptos.
            """,
            [(BTC, BEARISH), (ETH, BEARISH), (XRP, BEARISH)],
            id="All assets are bearish",
        ),
        pytest.param(
            """
            Bitcoin price is up 10% today.
            BTC is expected to continue its bullish trend.
            Nevertheless, XRP is not looking so good as BTC.
            """,
            [(BTC, BULLISH), (ETH, BULLISH)],
            id="BTC is bullish, ETH is neutral, XRP is bearish",
        ),
        pytest.param(
            """
            Ethereum and Bitcoin show strong momentum as Layer 1 solutions gain
            traction. ETH 2.0 staking hits new highs while BTC hashrate reaches
            record levels.
            """,
            [(BTC, BULLISH), (ETH, BULLISH)],
            id="BTC and ETH are bullish, XRP neutral",
        ),
        pytest.param(
            """
            SEC investigation into Ethereum's security status creates uncertainty.
            Ripple faces new legal challenges. Bitcoin trades sideways.
            """,
            [(ETH, BEARISH), (XRP, BEARISH)],
            id="BTC neutral, ETH and XRP bearish",
        ),
        pytest.param(
            """
            Ethereum surges on successful network upgrade.
            Meanwhile, Bitcoin consolidates at current levels.
            Ripple (XRP) drops 5% on profit taking.
            """,
            [(BTC, BEARISH), (ETH, BULLISH)],
            id="Mixed with emphasis on ETH",
        ),
        pytest.param(
            """
            New regulations target XRP and other altcoins specifically.
            Bitcoin remains unaffected due to commodity classification.
            ETH community debates potential regulatory impact.
            """,
            [(ETH, BEARISH), (XRP, BEARISH)],
            id="Regulatory news affecting specific assets",
        ),
        pytest.param(
            """
            Major institutional investors announce plans to increase crypto holdings,
            with focus on Bitcoin and Ethereum. Traditional finance continues to
            embrace digital assets.
            """,
            [(BTC, BULLISH), (ETH, BULLISH)],
            id="Institutional adoption favoring BTC and ETH",
        ),
        pytest.param(
            """
            Global economic uncertainty rises as inflation concerns grow.
            Bitcoin's narrative as digital gold strengthens while altcoins
            face selling pressure.
            """,
            [(BTC, BULLISH), (ETH, BEARISH)],
            id="Market uncertainty favoring BTC as safe haven",
        ),
        pytest.param(
            """
            Technical analysis shows crypto market entering oversold territory.
            Bitcoin's dominance index declining as altcoins gain momentum.
            XRP leads altcoin recovery.
            """,
            [(BTC, BEARISH), (ETH, BULLISH), (XRP, BULLISH)],
            id=" Altcoin season scenario",
        ),
        pytest.param(
            """
            Major crypto exchange faces regulatory scrutiny and potential fines.
            Trading volumes drop across all major cryptocurrencies amid
            growing concerns.
            """,
            [(BTC, BEARISH), (ETH, BEARISH), (XRP, BEARISH)],
            id=" Exchange FUD affecting entire market",
        ),
        pytest.param(
            """
            Ethereum gas fees hit record lows after successful network upgrade.
            Layer 2 solutions show promising adoption metrics.
            """,
            [(ETH, BULLISH)],
            id=" ETH-specific technical improvement",
        ),
        pytest.param(
            """
            Breaking: Major country announces complete ban on crypto trading.
            Bitcoin mining operations forced to relocate. Market impact yet
            to be determined.
            """,
            [(BTC, BEARISH), (ETH, BEARISH), (XRP, BEARISH)],
            id=" Regulatory crackdown primarily affecting BTC",
        ),
        pytest.param(
            """
            XRP wins landmark court inst regulatory body.
            Legal clarity expected to boost institutional adoption of
            regulated cryptocurrencies.
            """,
            [(XRP, BULLISH)],
            id=" XRP-specific positive legal development",
        ),
        pytest.param(
            """
            Cryptocurrency market experiences flash crash as major stablecoin
            loses dollar peg. All major assets affected in the short term.
            """,
            [(BTC, BEARISH), (ETH, BEARISH), (XRP, BEARISH)],
            id=" Systemic risk affecting all assets",
        ),
        pytest.param(
            """
            USD and EUR rise against major currencies, while Bitcoin falls
            """,
            [(BTC, BEARISH)],
            id="USD and EUR rise, Bitcoin falls",
        ),
    ],
)
def test_ollama_analyzer(
    ollama_analyzer: OllamaSentimentAnalyzer,
    story: str,
    expected_sentiments: list[tuple[Asset, Sentiment]],
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
    sentiments = {s.asset: s.sentiment for s in result.asset_sentiments}
    expected = {asset: sentiment.value for asset, sentiment in expected_sentiments}

    if sentiments != expected:
        pytest.fail(f"""
        Story: {story}

        BTC:
            Result: {sentiments.get(Asset.BTC)}
            Expected: {expected.get(Asset.BTC)}

        ETH:
            Result: {sentiments.get(Asset.ETH)}
            Expected: {expected.get(Asset.ETH)}

        XRP:
            Result: {sentiments.get(Asset.XRP)}
            Expected: {expected.get(Asset.XRP)}

        All:
            Result: {sentiments}
            Expected: {expected}
        """)
