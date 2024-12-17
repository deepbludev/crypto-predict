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
    
    Analyze the following news story and determine its potential impact ONLY on these specific assets:
    {assets}
    
    ⚠️ CRITICAL INSTRUCTION ⚠️
    You MUST COMPLETELY IGNORE any assets not in the above list, even if they are explicitly mentioned in the news.
    If the news only talks about non-listed assets, you MUST return an empty array [].
    
    Example:
    - If the news says "Solana rises 20%" but SOL is not in the asset list → return []
    - If the news says "Bitcoin and Solana rise 20%" and only BTC is in the asset list → only include BTC
    - If the news mentions USD, EUR, or any non-listed crypto → ignore them completely
    
    Possible sentiment signals: BULLISH, BEARISH
    
    Response Rules:
    1. First, check if an asset is in the allowed list: {assets}
    2. If the asset is not in this exact list → ignore it completely
    3. Only for assets in the allowed list, analyze if the news impacts them
    4. Return [] if:
       - The news only discusses non-listed assets
       - The news has no clear impact on any listed assets
       - You're unsure if the impact affects listed assets
    
    For the relevant ALLOWED assets only, provide a sentiment based on:
    
    BULLISH when:
    - The news suggests positive price movement
    - There are strong positive catalysts
    - The asset might benefit from positive market dynamics
    
    BEARISH when:
    - The news suggests negative price movement
    - There are concerning developments or risks
    - The asset might be negatively impacted by market conditions
    
    Response Format:
    - Must be a valid JSON array: [{{"asset": string, "sentiment": string}}]
    - "asset" must be EXACTLY one of: {assets}
    - "sentiment" must be either: "BULLISH" or "BEARISH"
    
    Examples of CORRECT responses for different scenarios:

    News: "Solana rises 20%"
    []
    # Empty array because SOL is not in allowed assets

    News: "USD/BTC pair shows strength"
    [
        {{"asset": "BTC", "sentiment": "BULLISH"}}
    ]
    # Only BTC is included because USD is not in allowed list

    News: "Solana, Cardano, and Dogecoin show massive gains"
    []
    # Empty array since none of the mentioned assets are in allowed list

    News: "Bitcoin drops 5% while Solana surges"
    [
        {{"asset": "BTC", "sentiment": "BEARISH"}}
    ]
    # Only BTC included, SOL ignored as it's not in allowed list

    News: "Crypto exchange updates its UI design"
    []
    # Empty array because no clear impact on any allowed assets

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
            asset_sentiments=[a for a in result.root if a.asset in Asset],
            llm_model=self.llm_model,
            story=story.title,
        )
