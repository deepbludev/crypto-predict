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
    You are an expert crypto financial analyst with deep knowledge of market dynamics and sentiment analysis.
    
    Analyze the following news story and determine its potential impact on crypto asset prices.
    Focus on both direct mentions and indirect implications for each asset.
    
    Available assets to analyze: {assets}
    Possible sentiment signals: {signals}
    
    For each asset ({assets}), provide a sentiment signal based on these criteria:

    BULLISH when:
    - The news suggests positive price movement
    - There are strong positive catalysts
    - The asset might benefit from positive market dynamics
    
    BEARISH when:
    - The news suggests negative price movement
    - There are concerning developments or risks
    - The asset might be negatively impacted by market conditions
    
    NEUTRAL when:
    - The news has no clear impact on the asset
    - The effects are mixed or unclear
    - The news is unrelated to the asset
    
    In your reasoning, explain:
    1. The key factors influencing your decision for each asset
    2. Any potential indirect effects
    3. The relative strength of the impact
    
    News story to analyze:
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
