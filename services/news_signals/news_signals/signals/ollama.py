from textwrap import dedent

from llama_index.core.prompts import PromptTemplate
from llama_index.llms.ollama import Ollama

from domain.llm import LLMModel
from domain.news import NewsStory
from domain.sentiment_analysis import (
    NewsStorySentimentAnalysis,
    SentimentAnalysisResult,
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

    def __init__(self, llm_model: LLMModel, base_url: str):
        self.llm = Ollama(model=llm_model, base_url=base_url, temperature=0)

        assets = ", ".join(a.value for a in Asset)
        signals = ", ".join(s.value for s in SentimentSignal)
        prompt = f"""
            You are an expert crypto financial analyst.
            
            You are given a news story and you need to provide a sentiment signal
            based on the impact of the news on the prices of the following crypto assets: {assets}.
            
            The result of the sentiment analysis for each asset should be one of the following: {signals}.

            Here is the news story:
            {{news_story}}
        """  # noqa

        self.prompt_template = PromptTemplate(template=dedent(prompt).strip())

        super().__init__(llm_model)

    def analyze(self, story: NewsStory) -> NewsStorySentimentAnalysis:
        result = self.llm.structured_predict(
            SentimentAnalysisResult, prompt=self.prompt_template, news_story=story.title
        )
        return NewsStorySentimentAnalysis(
            story=story.title,
            llm_model=self.llm_model,
            **result.model_dump(),
        )
