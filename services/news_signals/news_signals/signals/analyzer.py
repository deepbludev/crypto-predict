from textwrap import dedent

import pydantic
from llama_index.core.llms import LLM
from llama_index.core.prompts import PromptTemplate

from domain.llm import LLMModel
from domain.news import NewsStory
from domain.sentiment_analysis import (
    AssetSentimentAnalysisDetails,
    NewsStorySentimentAnalysis,
)
from domain.trades import Asset

assets = ", ".join(a.value for a in Asset)
prompt = f"""
    You are an expert crypto financial analyst with deep knowledge of market dynamics and sentiment analysis.
    
    Analyze the following news story and determine its potential impact on crypto asset prices.
    Focus on both direct mentions and indirect implications for each asset.
    
    Available assets to consider in the analysis: {assets}
    Possible sentiment signals: BULLISH, BEARISH
    
    CRITICAL: You must ONLY include assets from the provided list of available assets.
    Any other assets, even if mentioned in the news, must be ignored.
    
    Important Response Guidelines:
    - Only include assets that are in the available assets list - no exceptions
    - Only include assets in the response that are DIRECTLY or INDIRECTLY affected by the news
    - If the news has no clear impact on an asset (neutral), DO NOT include it in the response
    - If the news has no relevant impact on any assets, return an empty list []
    - The asset MUST be exactly as written in the available assets list, no variations allowed
    
    For the relevant assets, provide a sentiment signal based on these criteria:

    BULLISH when:
    - The news suggests positive price movement
    - There are strong positive catalysts
    - The asset might benefit from positive market dynamics
    
    BEARISH when:
    - The news suggests negative price movement
    - There are concerning developments or risks
    - The asset might be negatively impacted by market conditions
    
    When analyzing the news, consider:
    - Direct mentions and explicit effects on specific assets
    - Indirect implications and market dynamics
    - Cross-asset correlations and ecosystem effects
    - Only include assets where you can justify a clear BULLISH or BEARISH sentiment
    
    IMPORTANT: Your response must be a valid JSON array containing objects with exactly these fields:
    [
        {{"asset": string, "sentiment": string}}
    ]
    
    Where:
    - "asset" must be EXACTLY one of: {assets}
    - "sentiment" must be either: "BULLISH" or "BEARISH"
    
    Examples of valid responses:

    1. News: "Goldman Sachs wants to invest in Bitcoin and Ethereum, but not in XRP."
    [
        {{"asset": "BTC", "sentiment": "BULLISH"}},
        {{"asset": "ETH", "sentiment": "BULLISH"}},
        {{"asset": "XRP", "sentiment": "BEARISH"}}
    ]

    2. News: "Bitcoin mining difficulty increases by 10%"
    [
        {{"asset": "BTC", "sentiment": "BULLISH"}}
    ]
    
    3. News: "Crypto exchange updates its UI design"
    []

    Examples of INVALID responses:
    News: "USD and EUR rise against major currencies, while Bitcoin falls"
    [
        {{"asset": "USD", "sentiment": "BULLISH"}},  # WRONG - USD is not in available assets
        {{"asset": "EUR", "sentiment": "BULLISH"}},  # WRONG - EUR is not in available assets
    ]

    News: "Solana and Cardano show strong growth, while Dogecoin struggles"
    [
        {{"asset": "SOL", "sentiment": "BULLISH"}},  # WRONG - SOL is not in available assets
        {{"asset": "ADA", "sentiment": "BULLISH"}},  # WRONG - ADA is not in available assets
        {{"asset": "DOGE", "sentiment": "BEARISH"}}  # WRONG - DOGE is not in available assets
    ]
    # Correct response would be [] if none of the available assets are affected
    
    News story to analyze:
    {{news_story}}
    
    Response (valid JSON array only):
"""  # noqa


AssetSentimentAnalysisList = pydantic.RootModel[list[AssetSentimentAnalysisDetails]]
"""
A list of AssetSentimentAnalysis objects.
Used as the structured output type for the LLM.
"""


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
            output_cls=AssetSentimentAnalysisList,
            prompt=self.prompt_template,
            news_story=story.title,
        )
        return NewsStorySentimentAnalysis(
            asset_sentiments=result.root,
            llm_model=self.llm_model,
            story=story.title,
        )
