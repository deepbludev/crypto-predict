import json
import os
import random
from typing import Any

import pandas as pd
from loguru import logger
from tqdm import tqdm

from domain.news import NewsStory
from news_signals.signals import get_sentiment_analyzer
from news_signals.signals.analyzer import SentimentAnalyzer


def extract(num_stories: int, source_filename: str) -> list[str]:
    """
    Extracts a list of news stories from a CSV file and returns a list of story titles.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    source_csv_path = os.path.join(current_dir, "data", source_filename)
    logger.info(f"Loading CSV from: {source_csv_path}")

    df = pd.read_csv(source_csv_path)
    stories: list[str] = df["title"].tolist()
    stories = random.sample(stories, num_stories)
    logger.info(f"Loaded {len(stories)} stories")

    return stories


def transform(story_title: str, analyzer: SentimentAnalyzer) -> dict[str, Any]:
    """
    Transforms a news story title into an instruction dataset entry, by
    analyzing the story with the sentiment analyzer and returning the
    instruction, input, output, and teacher model name.
    """
    story = NewsStory.dummy(title=story_title)
    logger.info(f"Analyzing story: {story_title}")
    sentiment = analyzer.analyze(story)
    encoded_sentiments = [s.encoded() for s in sentiment.asset_sentiments]

    output = {
        "instruction": analyzer.base_prompt,
        "input": sentiment.story,
        "output": encoded_sentiments,
        "teacher_model_name": sentiment.llm_model,
    }
    logger.info(f"Ouput: {json.dumps(output['output'], indent=2)}")
    return output


def load(output: dict[str, Any], output_filename: str):
    """
    Loads the transformed story into a JSONL file.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_filename = os.path.join(current_dir, "output", output_filename)
    with open(output_filename, "a") as f:
        f.write(json.dumps(output) + "\n")


def etl(
    num_stories: int,
    source_filename: str,
    output_filename: str,
    analyzer: SentimentAnalyzer,
):
    stories = extract(num_stories, source_filename)

    for story in tqdm(stories):
        output = transform(story, analyzer=analyzer)
        load(output, output_filename)


if __name__ == "__main__":
    etl(
        num_stories=1000,
        source_filename="cryptopanic_news.csv",
        output_filename="cryptopanic_news_instruction_dataset.jsonl",
        analyzer=get_sentiment_analyzer(),
    )
