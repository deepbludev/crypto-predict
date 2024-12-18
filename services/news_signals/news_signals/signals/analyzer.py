import json
from textwrap import dedent

from llama_index.core.llms import LLM
from llama_index.core.prompts import PromptTemplate
from loguru import logger
from pydantic import ValidationError

from domain.llm import LLMName
from domain.news import NewsStory
from domain.sentiment_analysis import (
    AssetSentiment,
    NewsStorySentimentAnalysis,
)
from domain.trades import Asset

assets = ", ".join(a.value for a in Asset)
base_prompt = f"""
    You are an expert crypto financial analyst with deep knowledge of market dynamics and sentiment analysis.
    
    Analyze the following news story and determine its potential impact ONLY on these specific assets:
    {assets}
    
    ⚠️ CRITICAL INSTRUCTION #1⚠️
    You MUST COMPLETELY IGNORE any assets not in the above list, even if they are explicitly mentioned in the news.
    If the news only talks about non-listed assets, you MUST return an empty array [].
    
    ⚠️ CRITICAL INSTRUCTION #2⚠️
    Possible sentiment signals: BULLISH, BEARISH
    The sentiment signal must be either **"BULLISH"** or **"BEARISH"**, and not any other value.
    **Do not leave the "sentiment" field empty or include any other text.**
    
    Response Rules:
    1. First, check if an asset is in the allowed list: {assets}
    2. If the asset is not in this exact list → ignore it completely
    3. Only for assets in the allowed list, analyze if the news impacts them
    4. Return [] if:
        - The news only discusses non-listed assets
        - The news has no clear impact on any listed assets
        - You're unsure if the impact affects listed assets
    5. **Ensure that the "sentiment" field is either "BULLISH" or "BEARISH" and not any other value. Do not leave it empty.**
    
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
    - "asset" must be EXACTLY one of: {assets}
    - "sentiment" must be either: "BULLISH" or "BEARISH"
    - ONLY return the JSON array. Do NOT include any other text, notes or comments.
    
    Example of a valid response:
    [
        {{"asset": "BTC", "sentiment": "BULLISH"}},
        {{"asset": "ETH", "sentiment": "BEARISH"}}
    ]

"""  # noqa


class SentimentAnalyzer:
    def __init__(self, llm_name: LLMName, llm: LLM):
        self.llm = llm
        self.llm_name = llm_name
        self.base_prompt = base_prompt
        self.raw_prompt = dedent(f"""
            {self.base_prompt}
            
            News story to analyze:
            "{{news_story}}"
            
            Response (valid JSON array only):
        """).strip()  # noqa

        self.prompt_template = PromptTemplate(template=self.raw_prompt)

    def analyze(self, story: NewsStory) -> NewsStorySentimentAnalysis:
        """
        Analyze the sentiment of the given news story using the LLM model
        and the prompt template.

        Returns:
            NewsStorySentimentAnalysis: The sentiment analysis result.
        """
        # Get raw completion instead of structured prediction
        prompt = self.prompt_template.format(news_story=story.title)
        response = self.llm.complete(prompt=prompt)

        try:
            sentiments = [AssetSentiment(**s) for s in json.loads(response.text)]
        except (ValidationError, json.JSONDecodeError, KeyError, TypeError) as e:
            # Handle invalid responses
            logger.error(f"[{self.llm_name}] Invalid response:{e}")
            logger.error(response.text)
            sentiments = []

        return NewsStorySentimentAnalysis(
            asset_sentiments=sentiments,
            llm_name=self.llm_name,
            story=story.title,
        )
