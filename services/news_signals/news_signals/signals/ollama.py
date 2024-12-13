from textwrap import dedent

from llama_index.core.prompts import PromptTemplate
from llama_index.llms.ollama import Ollama

from domain.llm import LLMModel
from domain.news import NewsStory
from domain.sentiment_analysis import (
    NewsStorySentimentAnalysis,
    SentimentSignal,
)
from domain.trades import Asset

from .analyzer import SentimentAnalyzer

assets = [a.value for a in Asset]
signals = [s.value for s in SentimentSignal]
template = """
You are an expert crypto financial analyst.
You are given a news story and you need to provide a sentiment signal
based on the impact of the news on the prices of the following crypto assets: BTC, ETH, XRP.
The result of the sentiment analysis for each asset should be one of the following: BEARISH, NEUTRAL, BULLISH.

Here is the news story:
{news_story}
"""  # noqa: E501


class OllamaSentimentAnalyzer(SentimentAnalyzer):
    """Sentiment analyzer using Ollama."""

    def __init__(self, llm_model: LLMModel):
        self.llm = Ollama(model=llm_model, temperature=0)
        self.prompt_template = PromptTemplate(template=dedent(template).strip())

        super().__init__(llm_model)

    def analyze(self, story: NewsStory) -> NewsStorySentimentAnalysis:
        result = self.llm.structured_predict(
            NewsStorySentimentAnalysis,
            prompt=self.prompt_template,
            news_story=story.title,
        )
        print("result:", result)
        return NewsStorySentimentAnalysis.parse(result.model_dump())
