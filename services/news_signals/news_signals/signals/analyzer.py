from textwrap import dedent

from llama_index.core.llms import LLM
from llama_index.core.prompts import PromptTemplate

from domain.llm import LLMModel
from domain.news import NewsStory
from domain.sentiment_analysis import (
    NewsStorySentimentAnalysis,
    SentimentAnalysisResult,
    SentimentSignal,
)
from domain.trades import Asset

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


class SentimentAnalyzer:
    def __init__(self, llm_model: LLMModel, llm: LLM):
        self.llm = llm
        self.llm_model = llm_model
        self.prompt_template = PromptTemplate(template=dedent(prompt).strip())

    def analyze(self, story: NewsStory) -> NewsStorySentimentAnalysis:
        """
        Analyze the sentiment of the given news story using the LLM model
        and the prompt template.

        Returns:
            NewsStorySentimentAnalysis: The sentiment analysis result.
        """
        result = self.llm.structured_predict(
            SentimentAnalysisResult,
            prompt=self.prompt_template,
            news_story=story.title,
        )
        return NewsStorySentimentAnalysis(
            llm_model=self.llm_model,
            story=story.title,
            **result.model_dump(),
        )
