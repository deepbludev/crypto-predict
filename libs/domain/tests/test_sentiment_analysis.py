from domain.sentiment_analysis import SentimentAnalysisResult, SentimentSignal


def test_sentiment_analysis():
    sentiment_analysis = SentimentAnalysisResult(
        btc=SentimentSignal.BULLISH,
        eth=SentimentSignal.NEUTRAL,
        xrp=SentimentSignal.NEUTRAL,
        reasoning="The news is about Bitcoin and it is expected to go up.",
    )
    assert sentiment_analysis.btc == SentimentSignal.BULLISH
    assert sentiment_analysis.eth == SentimentSignal.NEUTRAL
    assert sentiment_analysis.xrp == SentimentSignal.NEUTRAL
