import pytest

from domain.llm import LLMModel
from domain.news import NewsOutlet, NewsStory
from domain.sentiment_analysis import SentimentSignal
from news_signals.signals.ollama import OllamaSentimentAnalyzer


@pytest.fixture
def ollama_analyzer() -> OllamaSentimentAnalyzer:
    return OllamaSentimentAnalyzer(llm_model=LLMModel.LLAMA_3_2_3B)


@pytest.mark.skip(reason="Ollama is not working")
def test_ollama_analyzer(ollama_analyzer: OllamaSentimentAnalyzer):
    story = NewsStory(
        outlet=NewsOutlet.CRYPTOPANIC,
        title="SEC approves Bitcoin ETF. Unprecedented move to boost crypto adoption.",
        source="Cryptopanic",
        published_at="2024-01-01",
        url="https://example.com",
    )

    result = ollama_analyzer.analyze(story)
    assert result.btc == SentimentSignal.BULLISH
    assert result.eth == SentimentSignal.NEUTRAL
    assert result.xrp == SentimentSignal.NEUTRAL
