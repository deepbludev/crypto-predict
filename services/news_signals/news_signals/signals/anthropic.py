from textwrap import dedent

from llama_index.core.prompts import PromptTemplate
from llama_index.llms.anthropic import Anthropic

from domain.llm import LLMModel
from domain.news import NewsStory
from domain.sentiment_analysis import (
    NewsStorySentimentAnalysis,
    SentimentSignal,
)
from domain.trades import Asset

from .analyzer import SentimentAnalyzer


class AnthropicSentimentAnalyzer(SentimentAnalyzer):
    """Sentiment analyzer using Anthropic."""

    def __init__(self, llm_model: LLMModel, api_key: str, temperature: float = 0):
        self.llm = Anthropic(model=llm_model, api_key=api_key, temperature=temperature)

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
            NewsStorySentimentAnalysis,
            prompt=self.prompt_template,
            news_story=story.title,
        )
        return NewsStorySentimentAnalysis.parse(result.model_dump())
