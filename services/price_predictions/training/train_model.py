from loguru import logger
from price_predictions.core.settings import Settings, price_predictions_settings
from price_predictions.fstore import PricePredictionsReader


def train(settings: Settings):
    """
    Train the Price Predictions model.

    This script will train the Price Predictions model using the feature view
    specified by the fview_name and fview_version.

    It has the following steps:
    1. Reads the feature data from the Feature Store.
    2. Splits the data into training and testing sets. #TODO: implement this step
    3. Trains the model using the training set. #TODO: implement this step
    4. Evaluates the model using the testing set. #TODO: implement this step
    5. Saves the model to the Model Registry. #TODO: implement this step

    For experiment tracking, it uses CometML.

    Args:
        fstore_project (str): The name of the Hopsworks project.
        fstore_api_key (str): The API key for the Hopsworks project.
        fview_name (str): The name of the feature view.
        fview_version (int): The version of the feature view.
    """
    logger.info("Training Price Predictions model")

    reader, days_back = PricePredictionsReader(settings), settings.days_back
    logger.info(f"Reading data from {days_back} days back")
    train_data = reader.train_data(days_back)

    # TODO: remove this once the rest of the steps are implemented
    logger.info(
        train_data[
            [
                "asset",
                "timeframe",
                "news_signal_llm_name",
                "news_signal_signal",
                "timestamp",
                "news_signal_timestamp",
            ]
        ]
    )


if __name__ == "__main__":
    settings = price_predictions_settings()
    train(settings)
